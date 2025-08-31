from abc import ABC, abstractmethod
from contextvars import ContextVar
from typing import Callable, Any, Optional
import cloudpickle
import hashlib
import sys
import uuid
from river_sdk.sandbox import BaseSandbox
from river_sdk.fingerprint import get_fp
from river_common.status import JobStatus
from river_common.shared import Status


class JobContext():
    context = ContextVar('job-context')

    def __init__(self, job: 'Job'):
        self._job = job

    def __enter__(self):
        self._token = JobContext.context.set(self._job)
        return self
    
    def __exit__(self, _exc_type, _exc_val, _exc_tb):
        JobContext.context.reset(self._token)

    @staticmethod
    def get_current():
        return JobContext.context.get()
    

class JobResult():
    def __init__(self, status: Status, origan_job_id: str, main_return: Any = None):
        self.status = status
        self.origan_job_id = origan_job_id
        self.main_return = main_return

    @property
    def ok(self) -> bool:
        return self.status == Status.SUCCESS
    
    def is_cache(self, job_id: str) -> bool:
        return self.origan_job_id == job_id


class Job(ABC):

    def __init__(
        self,
        name: str,
        sandbox_creator: Optional[Callable[[], BaseSandbox]] = None,
        upstreams: Optional[list['Job']] = None,
    ):
        self.name = name
        self.result: Optional[JobResult] = None
        self._upstreams: list[Job] = []
        self.status = Status.PENDING
        self.sandbox: Any = None  # Use Any to avoid forcing users to specify generic types
        self._sandbox_creator = sandbox_creator
        self.error: Optional[Exception] = None
        # TODO, here we are not in River context
        # self.set_status(Status.PENDING) 
            
        if upstreams:
            self._join(upstreams)

    @property
    def id(self) -> str:
        # Generate deterministic UUID based on object memory address
        # Same instance will always produce the same UUID
        namespace = uuid.NAMESPACE_OID
        obj_id = f"job-{id(self)}"
        return str(uuid.uuid5(namespace, obj_id))

    def set_status(self, status: Status, exception: Optional[Exception] = None):
        """Set the job status and export"""
        self.status = status
        
        # Import here to avoid circular dependency
        from river_sdk.river import get_current_river
        print("@@@@")
        print(self.result)
        job_status = JobStatus(
            id=self.id,
            origan_id=self.result.origan_job_id if self.result else None,
            name=self.name,
            parent_id=get_current_river().id,
            status=status,
        )
        
        if status == Status.FAILED and exception:
            job_status.set_failed(exception)
        
        job_status.export()
    
    def should_cache_result(self) -> bool:
        return self.result is not None and self.result.ok

    @abstractmethod
    def main(self) -> Any:
        """Abstract method that must be implemented by subclasses."""
        pass

    def run(self):
        from river_sdk.river import get_current_sandbox_manager
        # TODO: this could be a problem for async jobs
        if self.status == Status.RUNNING:
            raise RuntimeError(f"Job '{self.name}' is already running.")
        
        current_sandbox_manager = get_current_sandbox_manager()
        
        if not self._run_already_finished() and not self._should_skip_due_to_upstream():
            try:
                fp = get_fp(self)
                print("😄, fp " + fp)
                if current_sandbox_manager.snapshot_exists(fp):
                    print("😄😄, cache " + self.name)
                    cached_job_result = current_sandbox_manager.get_job_result_from_snapshot(fp)
                    self.result = cached_job_result
                    self.set_status(cached_job_result.status)
                    return
                if self._sandbox_creator:
                    self.sandbox = self._sandbox_creator()
                with JobContext(self):
                    self._execute_main()
                print('🚗')
                if self.result and self.should_cache_result():
                    current_sandbox_manager.set_job_result_to_sandbox(
                        self.sandbox,
                        self.result,
                    )
                if self.sandbox:
                    current_sandbox_manager.take_snapshot(self.sandbox, fp)
            except Exception as e:
                self.result = JobResult(
                    status=Status.FAILED,
                    origan_job_id=self.id,
                )
                self.error = e
                self.set_status(Status.FAILED, e)
            finally:
                if self.sandbox:
                    current_sandbox_manager.destory(self.sandbox)
        # TODO, what should be the return of run?
        # return self.status, self.result, self.error

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
        return self.status in (Status.SUCCESS, Status.FAILED, Status.SKIPPED)

    def _should_skip_due_to_upstream(self):
        for job in self._upstreams:
            job.run()
            if job.status in (Status.FAILED, Status.SKIPPED):
                self.result = JobResult(
                    status=Status.SKIPPED,
                    origan_job_id=self.id,
                )
                self.set_status(Status.SKIPPED)
                return True
        return False

    def _execute_main(self):
        self.set_status(Status.RUNNING)
        r = self.main()
        self.result = JobResult(
            status=Status.SUCCESS,
            origan_job_id=self.id,
            main_return=r,
        )
        self.set_status(Status.SUCCESS)


class JobContextError(Exception):
    """Raised when job context operations are called outside of a job context."""
    pass

def get_current_job() -> Job:
    """Get the current Job instance from context."""
    try:
        return JobContext.get_current()
    except LookupError:
        raise JobContextError("get_current_job() can only be called within a job context")
