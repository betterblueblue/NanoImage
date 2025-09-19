from __future__ import annotations
import json
import threading
import uuid
from pathlib import Path
from typing import Any, Dict

from fastapi import UploadFile

from ..config import settings
from ..models import Job, JobStatusResponse
from ..storage import (
    UPLOADS_DIR,
    RESULTS_DIR,
    job_json_path,
    save_upload_file,
    result_url,
)
from ..tasks import process_job_background


class JobService:
    def __init__(self):
        self._lock = threading.Lock()

    def enqueue(self, job_type: str, params: Dict[str, Any], upload: UploadFile) -> str:
        job_id = str(uuid.uuid4())
        input_dir = UPLOADS_DIR / job_id
        input_path = save_upload_file(upload, input_dir)

        job = Job(
            id=job_id,
            type=job_type,
            status="pending",
            progress=0,
            params=params or {},
            input_path=str(input_path),
            results=[],
            error=None,
        )
        self._write_job(job)

        # Start background thread placeholder (production: Celery task)
        process_job_background(job_id)
        return job_id

    def status(self, job_id: str) -> JobStatusResponse:
        data = self._read_job(job_id)
        return JobStatusResponse(
            id=data["id"],
            status=data["status"],
            progress=data.get("progress", 0),
            results=[str(u) for u in data.get("results", [])],
            error=data.get("error"),
        )

    # --- internal helpers ---
    def _write_job(self, job: Job) -> None:
        p = job_json_path(job.id)
        p.write_text(job.model_dump_json(indent=2), encoding="utf-8")

    def _read_job(self, job_id: str) -> Dict[str, Any]:
        p = job_json_path(job_id)
        if not p.exists():
            raise FileNotFoundError(f"Job {job_id} not found")
        return json.loads(p.read_text(encoding="utf-8"))


job_service = JobService()

