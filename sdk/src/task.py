from typing import Dict, Optional
from sdk.src.job import job_context

class ShellTask():
    def __init__(self, command: str, cwd: Optional[str] = None, executable: str = "bash", env: Optional[Dict[str, str]] = None):
        super().__init__()
        self._command = command
        self._cwd = cwd
        self._executable = executable
        self._env = env or {}

    def execute(self):
        job = job_context.get()
        sandbox = job.sandbox
        
        if sandbox is None:
            raise RuntimeError("No sandbox available for task execution")

        result = sandbox.execute(
            command=self._command,
            cwd=self._cwd,
            env=self._env
        )
        # TODO, raise error when result.ok is false
        return result
