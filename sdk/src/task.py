from typing import Dict, Optional
from sdk.src.job import job_context


class Task:
    def __init__(self):
        self._job_context = job_context.get()

class ShellTask(Task):
    def __init__(self, script: str, workdir: Optional[str] = None, shell: str = "/bin/bash", env: Optional[Dict[str, str]] = None):
        super().__init__()
        self._script = script
        self._workdir = workdir
        self._shell = shell
        self._env = env or {}

    def execute(self):
        data = {
            "type": "shell",
            "script": self._script,
            "workdir": self._workdir,
            "shell": self._shell,
            "env": self._env
        }
        print(data)
