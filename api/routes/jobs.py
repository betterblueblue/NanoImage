from __future__ import annotations
import json
from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from typing import Any, Dict

from ..models import CreateJobResponse, JobStatusResponse
from ..services.job_service import job_service

router = APIRouter(prefix="/api")


@router.post("/jobs", response_model=CreateJobResponse)
def create_job(
    type: str = Form(...),
    params: str = Form("{}"),
    file: UploadFile = File(...),
):
    try:
        parsed: Dict[str, Any] = json.loads(params or "{}")
    except Exception:
        raise HTTPException(status_code=400, detail="params must be JSON string")

    job_id = job_service.enqueue(type, parsed, file)
    return {"job_id": job_id}


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
def get_job(job_id: str):
    try:
        return job_service.status(job_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Job not found")

