import inspect

from contextvars import ContextVar
from enum import Enum
from typing import Callable, Any, Optional


job_context = ContextVar('river-job')

class Job:
    class Status(Enum):
        PENDING = "pending"
        RUNNING = "running"
        SUCCESS = "success"
        FAILED = "failed"
        SKIPPED = "skipped"

    def __init__(
        self,
        name: str,
        main: Callable[..., Any],
        upstreams: Optional[list['Job']] = None,
    ):
        self.name = name
        self._main = main
        self.result = None
        self._upstreams: list[Job] = []
        self.status = Job.Status.PENDING
        if upstreams:
            self._join(upstreams)

    def run(self, validate=True):
        token = job_context.set(self)
        # TODO: this could be a problem for async jobs
        if self.status == Job.Status.RUNNING:
            raise RuntimeError(f"Job '{self.name}' is already running.")

        if validate:
            self._validate_all()

        if not self._run_already_finished() and not self._should_skip_due_to_upstream():
            self._execute_main()

        job_context.reset(token)
        return self.status, self.result

    def _join(self, upstreams: list['Job']):
        for job in upstreams:
            cycle_path = self._find_cycle_path(job, self)
            if cycle_path:
                if cycle_path[0] is not cycle_path[-1]:
                    cycle_path.append(cycle_path[0])
                cycle_str = ' -> '.join(j.name for j in cycle_path)
                msg = f"Joining {job.name} would create a cycle with {self.name}: {cycle_str}"
                raise ValueError(msg)
            if job not in self._upstreams:
                self._upstreams.append(job)

    def _find_cycle_path(self, start: 'Job', target: 'Job', path=None) -> Optional[list['Job']]:
        if path is None:
            path = []
        path.append(start)
        if start is target:
            return path.copy()
        for upstream in start._upstreams:
            result = self._find_cycle_path(upstream, target, path)
            if result:
                return result
        path.pop()
        return None

    def _collect_all_upstreams(self):
        result = {}
        def dfs(job):
            for up in job._upstreams:
                if up.name in result:
                    if result[up.name] is not up:
                        raise ValueError(
                            f"Duplicate upstream job name detected: '{up.name}' in the upstreams of job '{self.name}'. Job names must be unique in the upstream graph."
                        )
                    continue  # same object, skip
                result[up.name] = up
                dfs(up)
        dfs(self)
        return result

    def _validate_all(self, visited=None):
        if visited is None:
            visited = set()
        if id(self) in visited:
            return
        visited.add(id(self))
        upstreams_by_name = self._collect_all_upstreams()
        sig = inspect.signature(self._main)
        missing = []
        for param in sig.parameters.values():
            if param.name == 'self':
                continue
            if param.name not in upstreams_by_name:
                missing.append(param.name)
        if missing:
            available = ', '.join(upstreams_by_name.keys())
            raise ValueError(f"Job '{self.name}' main() parameters {missing} do not match any upstream job name. Available job names: {available}")
        for job in self._upstreams:
            job._validate_all(visited)

    def _run_already_finished(self):
        return self.status in (Job.Status.SUCCESS, Job.Status.FAILED, Job.Status.SKIPPED)

    def _should_skip_due_to_upstream(self):
        for job in self._upstreams:
            job.run(validate=False)
            if job.status in (Job.Status.FAILED, Job.Status.SKIPPED):
                self.status = Job.Status.SKIPPED
                self.result = None
                return True
        return False

    def _prepare_main_kwargs(self):
        upstreams_by_name = self._collect_all_upstreams()
        sig = inspect.signature(self._main)
        kwargs = {}
        for param in sig.parameters.values():
            if param.name == 'self':
                kwargs['self'] = self
            elif param.name in upstreams_by_name:
                kwargs[param.name] = upstreams_by_name[param.name]
        return kwargs

    def _execute_main(self):
        self.status = Job.Status.RUNNING
        try:
            kwargs = self._prepare_main_kwargs()
            result = self._main(**kwargs)
            self.status = Job.Status.SUCCESS
            self.result = result
        except Exception as e:
            self.status = Job.Status.FAILED
            self.result = None
