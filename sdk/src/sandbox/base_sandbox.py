from abc import ABC, abstractmethod
from typing import Optional
from enum import Enum
from invoke.runners import Result


class BaseSandbox(ABC):
    def __init__(self):
        self.id: str = ""
    
    def create(self) -> str:
        """Create the sandbox and return its identity.
        
        Returns:
            str: The sandbox identity/ID
        """
        self.id = self._create_impl()
        return self.id
    
    @abstractmethod
    def _create_impl(self) -> str:
        """Implementation of sandbox create logic.
        
        Returns:
            str: The sandbox identity/ID
        """
        pass
    
    def destory(self) -> None:
        """Destory the sandbox."""
        self._destory_impl(self.id)
        self.id = ""
    
    @abstractmethod
    def _destory_impl(self, sandbox_id: str) -> None:
        """Implementation of sandbox destory logic.
        
        Args:
            sandbox_id: The sandbox identity/ID to end
        """
        pass

    def take_snapshot(self) -> str:
        """Task snapshot of current sandbox and return the id of snapshot."""
        return self._take_snapshot_impl(self.id)
        
    @abstractmethod
    def _take_snapshot_impl(self, sandbox_id: str) -> str:
        """Implementation of sandbox task_snapshot logic.

        Returns:
            str: The snapshot identity/ID
        """
        pass
    
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

class SandboxProxy:
    def __init__(self, sandbox: BaseSandbox):
        self._sandbox = sandbox
    
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
        return self._sandbox.execute(command, cwd, env)
    