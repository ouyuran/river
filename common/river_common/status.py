from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime, timezone

from river_common.shared import ModuleTypes, Status


class StatusBase(BaseModel):
    id: str
    origan_id: Optional[str] = None
    name: str
    parent_id: str | None = None
    status: Status = Status.PENDING
    type: ModuleTypes = ModuleTypes.TASK
    error: Optional[str] = None
    error_type: Optional[str] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        # Allow enum deserialization from string values
        use_enum_values = True

    def set_status(self, status: Status):
        self.status = status
        self.updated_at = datetime.now(timezone.utc)
        # Clear error fields when status is not FAILED
        if status != Status.FAILED:
            self.error = None
            self.error_type = None

    def set_failed(self, exception: Optional[Exception] = None):
        """Set status to FAILED with optional exception details"""
        self.set_status(Status.FAILED)
        if exception:
            self.error = str(exception)
            self.error_type = exception.__class__.__name__

    def is_cache(self) -> bool:
        return self.id == self.origan_id

    def export(self):
        print(self.model_dump_json(), flush=True)

class RiverStatus(StatusBase):
    type: ModuleTypes = ModuleTypes.RIVER

class JobStatus(StatusBase):
    type: ModuleTypes = ModuleTypes.JOB

class TaskStatus(StatusBase):
    type: ModuleTypes = ModuleTypes.TASK
