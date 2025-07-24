from abc import ABC, abstractmethod
from contextvars import ContextVar
from enum import Enum
from typing import Callable, Any, Optional
from sdk.src.sandbox.base_sandbox import BaseSandbox


class JobContext():
    context = ContextVar('job-context')

    def __init__(self, job: 'Job'):
        self._job = job

    def __enter__(self):
        self._token = JobContext.context.set(self._job)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        JobContext.context.reset(self._token)

    @staticmethod
    def get_current():
        return JobContext.context.get()


class Job(ABC):
    class Status(Enum):
        PENDING = "pending"
        RUNNING = "running"
        SUCCESS = "success"
        FAILED = "failed"
        SKIPPED = "skipped"

    def __init__(
        self,
        name: str,
        sandbox_creator: Optional[Callable[[], BaseSandbox]] = None,
        upstreams: Optional[list['Job']] = None,
    ):
        self.name = name
        self.result = None
        self._upstreams: list[Job] = []
        self.status = Job.Status.PENDING
        self.sandbox: Any = None  # Use Any to avoid forcing users to specify generic types
        self._sandbox_creator = sandbox_creator
        self.error: Optional[Exception] = None
        if upstreams:
            self._join(upstreams)

    @abstractmethod
    def main(self) -> Any:
        """Abstract method that must be implemented by subclasses."""
        pass

    def run(self):
        from sdk.src.river import get_current_sandbox_manager
        # TODO: this could be a problem for async jobs
        if self.status == Job.Status.RUNNING:
            raise RuntimeError(f"Job '{self.name}' is already running.")
        
        if not self._run_already_finished() and not self._should_skip_due_to_upstream():
            try:
                if self._sandbox_creator:
                    self.sandbox = self._sandbox_creator()
                with JobContext(self):
                    self._execute_main()
                if self.sandbox:
                    get_current_sandbox_manager().take_snapshot(self.sandbox)
            except Exception as e:
                self.status = Job.Status.FAILED
                self.result = None
                self.error = e
            finally:
                if self.sandbox:
                    get_current_sandbox_manager().destory(self.sandbox)

        print(self.name, self.status, self.result, self.error)
        return self.status, self.result, self.error

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

    def _run_already_finished(self):
        return self.status in (Job.Status.SUCCESS, Job.Status.FAILED, Job.Status.SKIPPED)

    def _should_skip_due_to_upstream(self):
        for job in self._upstreams:
            job.run()
            if job.status in (Job.Status.FAILED, Job.Status.SKIPPED):
                self.status = Job.Status.SKIPPED
                self.result = None
                return True
        return False

    def _execute_main(self):
        self.status = Job.Status.RUNNING
        result = self.main()
        self.status = Job.Status.SUCCESS
        self.result = result

class JobContextError(Exception):
    """Raised when job context operations are called outside of a job context."""
    pass

def get_current_job() -> Job:
    """Get the current Job instance from context."""
    try:
        return JobContext.get_current()
    except LookupError:
        raise JobContextError("get_current_job() can only be called within a job context")
