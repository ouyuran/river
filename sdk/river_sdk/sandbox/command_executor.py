from abc import ABC, abstractmethod
from typing import Optional
from invoke.runners import Result
from fabric import Connection


class CommandExecutor(ABC):
    """Abstract command executor interface"""

    # @abstractmethod
    # def connect(self) -> Connection:
    #     """Establish connection to command execution environment."""
    #     pass

    @abstractmethod
    def run(
        self, command: str, cwd: Optional[str] = None, env: Optional[dict[str, str]] = None
    ) -> Result:
        """Execute command and return result"""
        pass


class LocalCommandExecutor(CommandExecutor):
    """Local command executor"""

    def run(
        self, command: str, cwd: Optional[str] = None, env: Optional[dict[str, str]] = None
    ) -> Result:
        with Connection("localhost") as connection, connection.cd(cwd if cwd else '.'):
            result = connection.local(command, env=env or {}, hide=True, warn=True)
        return result if result else Result(exited=1, stderr=f"Local run returns None, command: {command}")


class RemoteCommandExecutor(CommandExecutor):
    """Remote command executor"""

    def __init__(
        self,
        host: str,
        user: Optional[str] = None,
        key_filename: Optional[str] = None,
        password: Optional[str] = None,
        port: int = 22,
    ):
        self.host = host
        self.user = user
        self.port = port
        self.connect_kwargs = {}
        if key_filename:
            self.connect_kwargs["key_filename"] = key_filename
        if password:
            self.connect_kwargs["password"] = password

    def run(
        self, command: str, cwd: Optional[str] = None, env: Optional[dict[str, str]] = None
    ) -> Result:
        connection_params = {
            "host": self.host,
            "user": self.user,
            "port": self.port,
            "connect_kwargs": self.connect_kwargs,
        }

        with Connection(**connection_params) as connection, connection.cd(cwd if cwd else '.'):
            result = connection.run(command, env=env or {}, hide=True, warn=True)
        return result
