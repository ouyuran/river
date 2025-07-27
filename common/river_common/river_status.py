from pydantic import BaseModel
from typing import Literal

from river_common.shared import ModuleTypes, Status


class RiverStatus(BaseModel):
    id: str
    name: str
    status: Status = Status.PENDING
    type: Literal[ModuleTypes.RIVER] = ModuleTypes.RIVER
    

    def set_status(self, status: Status):
        self.status = status

    def export(self):
        print(self.model_dump_json(), flush=True)
