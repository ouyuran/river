from enum import Enum


class ModuleTypes(Enum):
    RIVER = "river"
    JOB = "job"
    TASK = "task"

class Status(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
