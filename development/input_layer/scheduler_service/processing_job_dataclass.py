
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID


class JobStatus(Enum):
    """
    Enumeration representing the possible statuses of a processing job.

    Attributes:
        PENDING (str): Indicates that the job is waiting to be processed.
        RUNNING (str): Indicates that the job is currently being processed.
        COMPLETE (str): Indicates that the job has finished processing successfully.
        FAILED (str): Indicates that the job encountered an error during processing.
    """
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class ProcessingJobList:
    pass

# TODO 
@dataclass
class ProcessingJob:
    job_id: UUID
    document_id: UUID
    status: JobStatus
    processor_type: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    processing_config: dict[str, Any]

    def __post_init__(self):
        self.job_id = UUID(self.job_id)
        self.document_id = UUID(self.document_id)
        self.status = JobStatus(self.status)
        self.started_at = datetime.fromisoformat(self.started_at) if self.started_at else None
        self.completed_at = datetime.fromisoformat(self.completed_at) if self.completed_at else None
