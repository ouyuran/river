from pydantic import BaseModel
from typing import Literal

from river_common.shared import ModuleTypes, Status


class TaskStatus(BaseModel):
    id: str
    name: str
    parent_id: str
    status: Status = Status.PENDING
    type: Literal[ModuleTypes.TASK] = ModuleTypes.TASK

    def set_status(self, status: Status):
        self.status = status

    def export(self):
        print(self.model_dump_json())

