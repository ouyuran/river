from typing import Dict, Optional
from sdk.src.job import Job, job_context


class Task:
    def __init__(self):
        self._job: Job = job_context.get()

    def build_task(self):
        raise NotImplementedError

    def execute(self):
        task = self.build_task()
        rc, stdout, stderr = self._job.executor.execute_task(task)
        if rc != 0:
            raise Exception(f"Task {self._job.name} failed with exit code {rc}")
        return stdout


class ShellTask(Task):
    def __init__(self, script: str, cwd: Optional[str] = None, executable: str = "bash", env: Optional[Dict[str, str]] = None):
        super().__init__()
        self._script = script
        self._cwd = cwd
        self._executable = executable
        self._env = env or {}

    def build_task(self):
        processed_lines = [line.strip() for line in self._script.split('\n') if line.strip()]
        processed_script = ';'.join(processed_lines)
        task = {
            "type": "shell",
            "script": processed_script,
            "cwd": self._cwd,
            "executable": self._executable,
            "env": self._env
        }
        return task
