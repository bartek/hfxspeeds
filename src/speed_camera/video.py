import json
import os
import time

from google.cloud.storage.blob import Blob
from google.cloud.storage.bucket import Bucket
import cv2

def read_and_upload(bucket: Bucket, filepath: str):
    print(filepath)
    cap = cv2.VideoCapture(filepath)
    assert cap.isOpened(), "Failed to open video"

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    name = os.path.basename(filepath)
    blob = bucket.blob(name).upload_from_filename(filepath)

    # Success, write metadata for this video
    blob = bucket.blob(f"{name}.meta")
    blob.upload_from_string(json.dumps({
        "last_updated": int(time.time()),
        "attributes": {
            "width": width,
            "height": height,
            "length": length,
        },
    }))






