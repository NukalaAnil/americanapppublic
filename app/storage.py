import json

from azure.storage.blob import BlobServiceClient
from azure.storage.queue import QueueClient

from .config import (
    INPUT_CONTAINER,
    OUTPUT_CONTAINER,
    QUEUE_NAME,
    STATUS_CONTAINER,
    STORAGE_CONNECTION_STRING,
)

blob_service = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
queue_client = QueueClient.from_connection_string(STORAGE_CONNECTION_STRING, QUEUE_NAME)

def ensure_storage() -> None:
    for container_name in (INPUT_CONTAINER, OUTPUT_CONTAINER, STATUS_CONTAINER):
        blob_service.get_container_client(container_name).create_container()
    queue_client.create_queue()

def write_status(job_id: str, status: dict) -> None:
    blob_service.get_blob_client(STATUS_CONTAINER, f"{job_id}.json").upload_blob(
        json.dumps(status), overwrite=True, content_type="application/json"
    )

def read_status(job_id: str) -> dict | None:
    blob = blob_service.get_blob_client(STATUS_CONTAINER, f"{job_id}.json")
    if not blob.exists():
        return None
    return json.loads(blob.download_blob().readall())
