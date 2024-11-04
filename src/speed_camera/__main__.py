import argparse
import logging

from google.cloud import storage
from .aivideo import upload_and_annotate

logging.basicConfig(level=logging.INFO)

bucket_name = "hfxspeeds"

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

# TODO: Check for args.process, and do that. Otherwise, capture video and upload procedure
bucket.list_blobs()
for index, blob in enumerate(bucket.list_blobs()):
    if blob.name.endswith(".json") or blob.name.endswith(".meta"):
        continue
    logging.info("[%d] blob %s", index, blob.name)
    upload_and_annotate(bucket, blob)

