from abc import ABC, abstractmethod
from typing import Callable, Optional, TypeVar, TYPE_CHECKING
from functools import partial
from invoke.runners import Result

if TYPE_CHECKING:
    from sdk.src.job import Job

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
    def create(self) -> BaseSandbox:
        """Create the sandbox and return a BaseSandbox instance.
        
        Returns:
            BaseSandbox: A sandbox instance for executing commands
        """
        pass

    def forker(self, job: 'Job') -> Callable[[], BaseSandbox]:
        """Create a no-argument callable that forks the given sandbox.
        
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
    def take_snapshot(self, sandbox: BaseSandbox) -> str:
        """Task snapshot of current sandbox and return the id of snapshot."""
        pass
    