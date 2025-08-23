from abc import ABC, abstractmethod
from typing import Any, Callable, Optional, TypeVar, TYPE_CHECKING
from functools import partial
from invoke.runners import Result
from river_common.status import JobStatus

if TYPE_CHECKING:
    from river_sdk.job import Job

T = TypeVar('T', bound='BaseSandbox')

class BaseSandbox(ABC):
    def __init__(self, id: str):
        self.id: str = id

    @abstractmethod
    def execute(
        self,
        command: str,
        cwd: str,
        env: Optional[dict[str, str]] = None
    ) -> Result:
        """Execute the command in sandbox.

        Args:
            command: The command to execute
            cwd: Working directory for command execution
            env: Environment variables

        Returns:
            Result: Invoke Result class.
        """
        pass

    # @abstractmethod
    # def connect(self):
    #     """Connect to sandbox."""
    #     pass

class BaseSandboxManager(ABC):

    @abstractmethod
    def creator(self, config: Any) -> Callable[[], BaseSandbox]:
        pass
    
    @abstractmethod
    def create(self, config: Any) -> BaseSandbox:
        """Create the sandbox and return a BaseSandbox instance.
        
        Returns:
            BaseSandbox: A sandbox instance for executing commands
        """
        pass

    def forker(self, job: 'Job') -> Callable[[], BaseSandbox]:
        """Create a no-argument callable that forks the sandbox from given job.
        
        Args:
            sandbox: The sandbox to fork from
            
        Returns:
            A callable that when invoked will fork the sandbox
        """
        return partial(self.fork, job)

    @abstractmethod
    def fork(self, job: 'Job') -> BaseSandbox:
        """Fork a new sandbox from given one."""
        pass
    
    @abstractmethod
    def destory(self, sandbox: BaseSandbox) -> None:
        """Destory the sandbox."""
        pass

    @abstractmethod
    def take_snapshot(self, sandbox: BaseSandbox, fingerprint: str) -> str:
        """Task snapshot of current sandbox and return the id of snapshot."""
        pass

    @abstractmethod
    def snapshot_exists(self, fingerprint: str) -> bool:
        """Check whether snapshot with given fingerprint exists."""
        pass
    
    @abstractmethod
    def set_job_status_to_sandbox(self, status: JobStatus) -> None:
        """Set job status to a sandbox instance."""
        pass

    @abstractmethod
    def get_job_status_from_snapshot(self, fingerprint: str) -> JobStatus:
        """Get job status from a snapshot with given fingerprint."""
        pass