import json
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from .config import INPUT_CONTAINER, OUTPUT_CONTAINER
from .storage import blob_service, ensure_storage, queue_client, read_status, write_status

def process_job(message: dict) -> None:
    job_id = message["job_id"]
    input_blob = message["input_blob"]
    preset = message["preset"]
    status = read_status(job_id) or {"job_id": job_id}
    status.update({"status": "processing", "started_at": datetime.now(timezone.utc).isoformat()})
    write_status(job_id, status)

    with tempfile.TemporaryDirectory() as temporary_directory:
        input_path = Path(temporary_directory) / "input.media"
        output_name = "output.mp4" if preset == "web" else "output.mp3"
        output_path = Path(temporary_directory) / output_name
        blob_service.get_blob_client(INPUT_CONTAINER, input_blob).download_blob().readinto(
            input_path.open("wb")
        )
        command = ["ffmpeg", "-y", "-i", str(input_path)]
        command += ["-c:v", "libx264", "-preset", "fast", "-c:a", "aac"] if preset == "web" else [
            "-vn", "-codec:a", "libmp3lame", "-b:a", "192k"
        ]
        command.append(str(output_path))
        subprocess.run(command, check=True, capture_output=True, text=True)
        output_blob = f"{job_id}/{output_name}"
        blob_service.get_blob_client(OUTPUT_CONTAINER, output_blob).upload_blob(
            output_path.open("rb"), overwrite=True
        )

    status.update({"status": "completed", "output_blob": output_blob, "completed_at": datetime.now(timezone.utc).isoformat()})
    write_status(job_id, status)

def run() -> None:
    ensure_storage()
    while True:
        messages = queue_client.receive_messages(messages_per_page=1, visibility_timeout=900)
        received = False
        for message in messages:
            received = True
            try:
                process_job(json.loads(message.content))
            except Exception as error:
                job_id = json.loads(message.content)["job_id"]
                status = read_status(job_id) or {"job_id": job_id}
                status.update({"status": "failed", "error": str(error)})
                write_status(job_id, status)
            finally:
                queue_client.delete_message(message)
        if not received:
            time.sleep(10)

if __name__ == "__main__":
    run()
