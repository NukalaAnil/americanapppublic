import os

STORAGE_CONNECTION_STRING = os.environ["AZURE_STORAGE_CONNECTION_STRING"]
INPUT_CONTAINER = os.getenv("INPUT_CONTAINER", "inputs")
OUTPUT_CONTAINER = os.getenv("OUTPUT_CONTAINER", "outputs")
STATUS_CONTAINER = os.getenv("STATUS_CONTAINER", "status")
QUEUE_NAME = os.getenv("QUEUE_NAME", "transcode-jobs")
