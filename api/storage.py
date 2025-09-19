from __future__ import annotations
from pathlib import Path
from typing import Iterable
import shutil

from fastapi import UploadFile

from .config import settings


BASE_DIR = Path(settings.STORAGE_DIR)
UPLOADS_DIR = BASE_DIR / "uploads"
RESULTS_DIR = BASE_DIR / "results"
JOBS_DIR = BASE_DIR / "jobs"

for d in (UPLOADS_DIR, RESULTS_DIR, JOBS_DIR):
    d.mkdir(parents=True, exist_ok=True)


def save_upload_file(upload: UploadFile, dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    target = dest_dir / upload.filename
    with target.open("wb") as f:
        shutil.copyfileobj(upload.file, f)
    return target


def save_bytes(content: bytes, dest_path: Path) -> Path:
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.write_bytes(content)
    return dest_path


def job_json_path(job_id: str) -> Path:
    return JOBS_DIR / f"{job_id}.json"


def result_url(path: Path) -> str:
    #  Serve via FastAPI StaticFiles mounted at /files
    rel = path.relative_to(BASE_DIR)
    return f"/files/{rel.as_posix()}"


def clean_dir(dir_path: Path, keep: Iterable[Path] | None = None) -> None:
    keep = set(keep or [])
    for p in dir_path.glob("*"):
        if p not in keep:
            if p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
            else:
                p.unlink(missing_ok=True)

