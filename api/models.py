from pydantic import BaseModel
from typing import Any, Dict, List, Optional, Literal

JobStatus = Literal["pending", "running", "finished", "failed"]


class Job(BaseModel):
    id: str
    type: str
    status: JobStatus
    progress: int = 0
    params: Dict[str, Any] = {}
    input_path: Optional[str] = None
    results: List[str] = []  # URL list
    error: Optional[str] = None


class CreateJobResponse(BaseModel):
    job_id: str


class JobStatusResponse(BaseModel):
    id: str
    status: JobStatus
    progress: int
    results: List[str] = []
    error: Optional[str] = None

