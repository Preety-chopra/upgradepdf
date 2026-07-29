from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.job import JobOperation, JobStatus


class JobResponse(BaseModel):
    id: str
    task_id: Optional[str]
    operation: JobOperation
    status: JobStatus
    input_filename: Optional[str]
    output_filename: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    purged_at: Optional[datetime]
    download_url: Optional[str] = None
    input_size_bytes: Optional[int] = None
    output_size_bytes: Optional[int] = None
    savings_percent: Optional[float] = None

    class Config:
        from_attributes = True