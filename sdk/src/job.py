import inspect

from contextvars import ContextVar
from enum import Enum
from typing import Callable, Any, Optional
from sdk.src.sandbox.base_sandbox import BaseSandbox
from sdk.src.sandbox.docker_sandbox import DockerSandboxManager


job_context = ContextVar('river-job')
docker_sandbox_manager = DockerSandboxManager("ubuntu")

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
        sandbox_creator: Optional[Callable[[], BaseSandbox]] = None,
        upstreams: Optional[dict[str, 'Job']] = None,
    ):
        self.name = name
        self._main = main
        self.result = None
        self._upstreams: dict[str, Job] = {}
        self.status = Job.Status.PENDING
        self.sandbox: Any = None  # Use Any to avoid forcing users to specify generic types
        self._sandbox_creator = sandbox_creator
        self.error: Optional[Exception] = None
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
            try:
                if self._sandbox_creator:
                    self.sandbox = self._sandbox_creator()
                self._execute_main()
                if self.sandbox:
                    docker_sandbox_manager.take_snapshot(self.sandbox)
                # TODO, take snapshot here, maybe we should set SandboxManager to current river context?
                # Rivers holds manager and Job uses it
                # Job holds sandbox and Taks uses it
            except Exception as e:
                self.status = Job.Status.FAILED
                self.result = None
                self.error = e

        job_context.reset(token)
        print(self.name, self.status, self.result, self.error)
        return self.status, self.result, self.error

    def _join(self, upstreams: dict[str, 'Job']):
        for key, job in upstreams.items():
            cycle_path = self._find_cycle_path(job, self)
            if cycle_path:
                if cycle_path[0] is not cycle_path[-1]:
                    cycle_path.append(cycle_path[0])
                cycle_str = ' -> '.join(j.name for j in cycle_path)
                msg = f"Joining {job.name} would create a cycle with {self.name}: {cycle_str}"
                raise ValueError(msg)
            if key not in self._upstreams:
                self._upstreams[key] = job

    def _find_cycle_path(self, start: 'Job', target: 'Job', path=None) -> Optional[list['Job']]:
        if path is None:
            path = []
        path.append(start)
        if start is target:
            return path.copy()
        for upstream in start._upstreams.values():
            result = self._find_cycle_path(upstream, target, path)
            if result:
                return result
        path.pop()
        return None


    def _validate_all(self, visited=None):
        if visited is None:
            visited = set()
        if id(self) in visited:
            return
        visited.add(id(self))
        sig = inspect.signature(self._main)
        missing = []
        for param in sig.parameters.values():
            if param.name == 'self':
                continue
            if param.name not in self._upstreams:
                missing.append(param.name)
        if missing:
            available = ', '.join(self._upstreams.keys())
            raise ValueError(f"Job '{self.name}' main() parameters {missing} do not match any upstream key. Available keys: {available}")
        for job in self._upstreams.values():
            job._validate_all(visited)

    def _run_already_finished(self):
        return self.status in (Job.Status.SUCCESS, Job.Status.FAILED, Job.Status.SKIPPED)

    def _should_skip_due_to_upstream(self):
        for job in self._upstreams.values():
            job.run(validate=False)
            if job.status in (Job.Status.FAILED, Job.Status.SKIPPED):
                self.status = Job.Status.SKIPPED
                self.result = None
                return True
        return False

    def _prepare_main_kwargs(self):
        sig = inspect.signature(self._main)
        kwargs = {}
        for param in sig.parameters.values():
            if param.name == 'self':
                kwargs['self'] = self
            elif param.name in self._upstreams:
                kwargs[param.name] = self._upstreams[param.name]
        return kwargs

    def _execute_main(self):
        self.status = Job.Status.RUNNING
        kwargs = self._prepare_main_kwargs()
        result = self._main(**kwargs)
        self.status = Job.Status.SUCCESS
        self.result = result
