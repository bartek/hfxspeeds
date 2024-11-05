from enum import Enum
import argparse
import json
import logging

from google.cloud import storage

from .aivideo import intelligence_annotate, annotate_video

from google.cloud.storage.blob import Blob
from google.cloud.storage.bucket import Bucket

logging.basicConfig(level=logging.INFO)

bucket_name = "hfxspeeds"

class BlobState(Enum):
    PENDING = "pending"
    # NEEDS_ANNOTATION is when file has been processed by Google Video AI (and
    # annotations exist), but have not been processed against the original
    # video.
    NEEDS_ANNOTATION = "needs_annotation"
    PROCESSED = "processed"
    FAILED = "failed"


# Flow
# When application is running, we want to be capturing videos. These are stored on device
# There is the fetch video and upload to AI Video / annotate loop
# This is a couple of parts, as we need to upload to AI video, get back results, and then run our own annotations to determine speed
# Before eventually having a resulting file.

# This is rudamentary but will get us going before making it fancy with realtime processing etc. Gotta start somewhere!
# So, decisions:
# 1. When recording video, we should have this be a separate
# application/process. The process will record video and chunk it at defined
# interval, saving onto the desired location (either on device or cloud),
# ideally abstract away the stuff with a blobstore
#
# 2. A separate program will be the video processor, which will read videos
# from provided source and run them through the upload/annotate process, save
# those results, and then run the final video writer annotationo
#
# Let's ignore video recorder for now as we're using a static video as a sample, and instead improve the whole lop

parser = argparse.ArgumentParser(description="Track speed of vehicles in video")
parser.add_argument("--process", type=bool, help="Process videos stored on bucket")
args = parser.parse_args()


storage_client = storage.Client()
bucket = storage_client.bucket(bucket_name)

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

# TODO: Check for args.process, and do that. Otherwise, capture video and upload procedure
bucket.list_blobs()
for index, blob in enumerate(bucket.list_blobs()):
    if blob.name.endswith(".json") or blob.name.endswith(".meta"):
        continue
    logging.info("[%d] blob %s", index, blob.name)
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
