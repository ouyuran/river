from typing import Callable, Any
from .task import ShellTask

class Job:
    def __init__(self, name: str, main: Callable[['Job'], Any]):
        self.name = name
        self.main = main
        self.results = []
        self._upstreams: list[Job] = []

    def join(self, jobs: list['Job']):
        for job in jobs:
            if self._has_path_to(job, self):
                raise ValueError(f"Joining {job.name} would create a cycle with {self.name}")
            if job not in self._upstreams:
                self._upstreams.append(job)

    def _has_path_to(self, start: 'Job', target: 'Job') -> bool:
        if start is target:
            return True
        for upstream in start._upstreams:
            if self._has_path_to(upstream, target):
                return True
        return False

    def run(self):
        for job in self._upstreams:
            job.run()
        return self.main(self)

    def run_task(self, task: ShellTask):
        result = task.execute() if hasattr(task, 'execute') else None
        self.results.append(result)
        return result
