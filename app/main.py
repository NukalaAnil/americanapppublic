import json
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from .config import INPUT_CONTAINER, QUEUE_NAME
from .storage import blob_service, ensure_storage, queue_client, read_status, write_status

app = FastAPI(title="Media Transcoding API", version="0.1.0")

@app.on_event("startup")
def startup() -> None:
    ensure_storage()

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

@app.post("/jobs", status_code=202)
async def create_job(file: UploadFile = File(...), preset: str = Form("web")) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="A filename is required")
    if preset not in {"web", "audio"}:
        raise HTTPException(status_code=400, detail="preset must be web or audio")

    job_id = str(uuid.uuid4())
    input_blob = f"{job_id}/{file.filename}"
    blob_service.get_blob_client(INPUT_CONTAINER, input_blob).upload_blob(
        await file.read(), overwrite=False
    )
    status = {
        "job_id": job_id,
        "status": "queued",
        "preset": preset,
        "input_blob": input_blob,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    write_status(job_id, status)
    queue_client.send_message(json.dumps({"job_id": job_id, "preset": preset, "input_blob": input_blob}))
    return status

@app.get("/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    status = read_status(job_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return status
