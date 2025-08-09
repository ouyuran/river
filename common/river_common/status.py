from pydantic import BaseModel
from typing import Literal, Optional

from river_common.shared import ModuleTypes, Status


class StatusBase(BaseModel):
    id: str
    name: str
    parent_id: str | None = None
    status: Status = Status.PENDING
    type: ModuleTypes = ModuleTypes.TASK
    error: Optional[str] = None
    error_type: Optional[str] = None

    def set_status(self, status: Status):
        self.status = status
        # Clear error fields when status is not FAILED
        if status != Status.FAILED:
            self.error = None
            self.error_type = None

    def set_failed(self, exception: Optional[Exception] = None):
        """Set status to FAILED with optional exception details"""
        self.status = Status.FAILED
        if exception:
            self.error = str(exception)
            self.error_type = exception.__class__.__name__
        else:
            self.error = None
            self.error_type = None

    def export(self):
        print(self.model_dump_json(), flush=True)

class RiverStatus(StatusBase):
    type: Literal[ModuleTypes.RIVER] = ModuleTypes.RIVER

class JobStatus(StatusBase):
    type: Literal[ModuleTypes.JOB] = ModuleTypes.JOB

class TaskStatus(StatusBase):
    type: Literal[ModuleTypes.TASK] = ModuleTypes.TASK
