from contextvars import ContextVar
from typing import Optional, Any, Callable, Mapping
import uuid
from river_sdk.sandbox.base_sandbox import BaseSandbox, BaseSandboxManager
from river_sdk.job import Job
from river_common.status import RiverStatus
from river_common.shared import Status


class RiverContext():
    context = ContextVar('river-context')

    def __init__(self, river: 'River'):
        self._river = river

    def __enter__(self):
        self._token = RiverContext.context.set(self._river)
        return self
    
    def __exit__(self, _exc_type, _exc_val, _exc_tb):
        RiverContext.context.reset(self._token)

    @staticmethod
    def get_current():
        return RiverContext.context.get()
        

class River:
    def __init__(
        self, 
        name: str,
        sandbox_manager: BaseSandboxManager,
        outlets: Mapping[str, Job],
        default_sandbox_config: Any = None,
        max_parallel_jobs: int = 1,
    ):
        self.id = str(uuid.uuid4())
        self.name = name
        self.sandbox_manager = sandbox_manager
        self.outlets = outlets
        self.default_sandbox_config = default_sandbox_config
        self.max_parallel_jobs = max_parallel_jobs
        self._default_sandbox_creator = None
        self.set_status(Status.PENDING)


    def set_status(self, status: Status, exception: Optional[Exception] = None):
        """Set the river status and export"""
        river_status = RiverStatus(
            id=self.id,
            name=self.name,
            status=status
        )
        
        if status == Status.FAILED and exception:
            river_status.set_failed(exception)
        
        river_status.export()
    
    def flow(self, outlet: str = "default") -> None:
        """Flow the river to the specified outlet (default: 'default')"""
        if outlet not in self.outlets:
            available = list(self.outlets.keys())
            raise ValueError(f"Outlet '{outlet}' not found. Available outlets: {available}")
        
        target_job = self.outlets[outlet]
        
        try:
            self.set_status(Status.RUNNING)
            with RiverContext(self):
                self.run_job(target_job)
            self.set_status(Status.SUCCESS)
        except Exception as e:
            self.set_status(Status.FAILED, e)
            raise
        
    def run_job(self, job: Job):
        """Call the run() of target job."""
        job.run()


class RiverContextError(Exception):
    """Raised when river context operations are called outside of a river context."""
    pass

def get_current_river() -> River:
    """Get the current River instance from context."""
    try:
        return RiverContext.get_current()
    except LookupError:
        raise RiverContextError("get_current_river() can only be called within a river context")

def get_current_sandbox_manager() -> BaseSandboxManager:
    """Get the current sandbox manager from the river context."""
    return get_current_river().sandbox_manager

def default_sandbox_creator() -> Callable[[], BaseSandbox]:
    """Get the default sandbox creator function."""
    def create_sandbox() -> BaseSandbox:
        manager = get_current_sandbox_manager()
        config = get_current_river().default_sandbox_config
        return manager.create(config)
    
    return create_sandbox

def sandbox_forker(job: Job) -> Callable[[], BaseSandbox]:
    """Create a no-argument callable that forks the sandbox from given job."""
    def fork_sandbox() -> BaseSandbox:
        manager = get_current_sandbox_manager()
        return manager.fork(job)
    
    return fork_sandbox
