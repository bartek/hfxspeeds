from enum import Enum
import cv2
import json
import logging
import os
import tempfile
import time

from tqdm import tqdm
from google.cloud import videointelligence_v1 as videointelligence
from google.cloud import storage
from google.cloud.storage.blob import Blob
from google.cloud.storage.bucket import Bucket

from .annotations import extract_cars, bb_centroid

from libcloud.storage.base import Object

bucket_name = "hfxspeeds"

video_client = videointelligence.VideoIntelligenceServiceClient()

# Blue color in BGR
color = (255, 0, 0)

# Line thickness of 2 px
thickness = 10

def normalised_to_xy(x, y, width, height):
    return int(x * width), int(y * height)

def box_start(box, width, height):
    return normalised_to_xy(box["left"], box["top"], width, height)

def box_end(box, width, height):
    return normalised_to_xy(box["right"], box["bottom"], width, height)

class BlobState(Enum):
    PENDING = "pending"
    # NEEDS_ANNOTATION is when file has been processed by Google Video AI (and
    # annotations exist), but have not been processed against the original
    # video.
    NEEDS_ANNOTATION = "needs_annotation"
    PROCESSED = "processed"
    FAILED = "failed"

def annotate_video(bucket: Bucket, blob: Blob):
    frame_rate = 30
    distance = 20 # Need to measure distance captured in video
    min_speed = 5 # kmph
    min_distance = 0

    # iPhone Vertical, exported
    width = 360
    height = 630 
    # 360 640 29.994497340381184 8994 (w/h/fps/l)

    annotations_file = bucket.get_blob(f"annotations/{blob.name}.json")
    assert annotations_file is not None, "Expected annotations file does not exist"

    annotations = json.loads(annotations_file.download_as_string().decode('utf-8'))

    cars_frame_lookup = extract_cars(annotations, frame_rate, distance, min_speed, min_distance)

    temp = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(blob.name)[1])
    temp_path = temp.name
    temp.close()

    # Download from GCS
    b = bucket.get_blob(blob.name)
    assert b is not None, "Expected blob does not exist"
    b.download_to_filename(temp_path)

    #out_path = tempfile.NamedTemporaryFile(delete=False, suffix="mp4")
    out_path = "/tmp/annotated.mp4"

    cap = cv2.VideoCapture(temp_path)
    assert cap.isOpened(), "Failed to open video"

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # 360 640 29.994497340381184 8994
    print(width, height, frame_rate, length)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Use MP4V codec
    dest = cv2.VideoWriter(out_path, fourcc, frame_rate, (width, height))
    assert dest.isOpened(), "Failed to open output video"

    def frame_iter():
        while True:
            ret, frame = cap.read()
            if ret is False:
                break
            yield frame

    frame_number = 0
    logging.info(f"annotating video with {length} frames")
    for frame in tqdm(frame_iter(), total=length):
        logging.debug("annotating frame #%s", frame_number)
        for idx, car in enumerate(cars_frame_lookup):
            if frame_number in car:
                logging.info("car #%s = %s", idx, car[frame_number])
                frame = cv2.rectangle(
                    frame,
                    box_start(car[frame_number], width, height),
                    box_end(car[frame_number], width, height),
                    color,
                    thickness,
                )
                frame = cv2.putText(
                    frame,
                    "car " + str(idx) + " speed: " + str(car["car_speed"]) + "km/h",
                    box_start(car[frame_number], width, height),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    2.0,
                    (0, 0, 0),
                    4,
                )
                centroid = bb_centroid(car[frame_number])
                coords = normalised_to_xy(centroid[0], centroid[1], width, height)
                frame = cv2.circle(
                    frame, coords, radius=10, color=(255, 255, 255), thickness=-1
                )
        dest.write(frame)
        frame_number += 1

    cap.release()
    dest.release()
    print(out_path)

    return temp_path


def intelligence_annotate(bucket: Bucket, blob: Blob):
    config = videointelligence.ObjectTrackingConfig()
    context = videointelligence.VideoContext(object_tracking_config=config)

    output_uri = f"gs://hfxspeeds/annotations/{blob.name}.json"
    operation = video_client.annotate_video(request={
        "features": [videointelligence.Feature.OBJECT_TRACKING],
        "input_uri": f"gs://hfxspeeds/{blob.name}",
        "output_uri": output_uri,
        "video_context": context,
    })

    operation.result(timeout=1200) # Blocking

    # Success, write to the state file with the annotations path
    blob = bucket.blob(f"{blob.name}.meta")
    blob.upload_from_string(json.dumps({
        "annotations": output_uri,
        "last_updated": int(time.time())
    }))

    print(operation)

# Obtain state about object in bucket.
def object_state(bucket: Bucket, blob: Blob) -> BlobState:
    state_file = bucket.get_blob(f"{blob.name}.meta")
    if state_file is None:
        return BlobState.PENDING

    contents = json.loads(state_file.download_as_string().decode('utf-8'))
    print(contents)

    # Otherwise, read the file. It's just JSON with some data:
    # {
    #   "annotations": "gs://bucket/path/to/annotations.json",
    #   ... other results file
    #   "last_updated": int64
    # }
    if 'annotations' in contents and 'output' not in contents:
        return BlobState.NEEDS_ANNOTATION

    return BlobState.PROCESSED

def upload_and_annotate(bucket: Bucket, blob: Blob):
    match object_state(bucket, blob):
        case BlobState.PENDING:
            # Upload this to Video AI API
            logging.info("Processing %s with Video AI API", blob.name)
            intelligence_annotate(bucket, blob)
        case BlobState.NEEDS_ANNOTATION:
            logging.info("Blob %s is currently processing, skipping", blob.name)
            annotate_video(bucket, blob)
        case BlobState.PROCESSED:
            logging.info("Blob %s is already processed", blob.name)
        case BlobState.FAILED:
            logging.info("Blob %s failed processing", blob.name)

