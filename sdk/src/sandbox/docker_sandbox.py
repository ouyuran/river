import uuid

from fabric import Connection
from functools import partial
from typing import Callable, Optional, TYPE_CHECKING
from sdk.src.sandbox.command_executor import CommandExecutor, LocalCommandExecutor, RemoteCommandExecutor
from invoke.runners import Result
from sdk.src.sandbox.base_sandbox import BaseSandbox, BaseSandboxManager

if TYPE_CHECKING:
    from sdk.src.job import Job


class DockerSandbox(BaseSandbox):
    def __init__(self, id: str, executor: CommandExecutor):
        super().__init__(id)
        self._executor: CommandExecutor = executor
        self._connection: Optional[Connection] = None
        self._snapshot: Optional[str] = None

    def execute(
        self,
        command: str,
        cwd: Optional[str] = None,
        env: Optional[dict[str, str]] = None
    ) -> Result:
        """Generate docker exec command"""
        docker_cmd = f"docker exec"
        
        # Add environment variables
        if env:
            for key, value in env.items():
                docker_cmd += f" -e {key}={value}"
        
        # TODO, add test for cwd == None
        docker_cmd += f" -w {cwd if cwd is not None else '/'}"
        # TODO, docker_cmd += f" {self.id} bash -c {shlex.quote(command)}"
        docker_cmd += f" {self.id} bash -c \"{command}\""
        
        return self._executor.run(docker_cmd)
    
    @property
    def snapshot(self) -> Optional[str]:
        return self._snapshot
    
    @snapshot.setter
    def snapshot(self, tag: str):
        self._snapshot = tag
    

class DockerSandboxManager(BaseSandboxManager):
    def __init__(self, image: str, host: str = "localhost"):
        super().__init__()
        # TODO, remove this one
        self.image: str = image
        self._host: str = host
        self._executor: CommandExecutor = self._create_executor(host)
    
    def _create_executor(self,host: str) -> CommandExecutor:
        return LocalCommandExecutor() if host == "localhost" else RemoteCommandExecutor(host)
    
    def create(self, image: str) -> DockerSandbox:
        """Start a Docker container.
        
        Args:
            image: docker image.

        Returns:
            DockerSandBox: The representation of the started container.
        """
        result = self._executor.run(f"docker run -d {image} sleep infinity")
        container_id = result.stdout.strip()
        return DockerSandbox(
            id=container_id,
            # Create new executor instance to isolate manager and sandbox
            executor=self._create_executor(self._host)
        )
    
    def fork(self, job: 'Job') -> DockerSandbox:
        sandbox = job.sandbox
        if sandbox is None:
            msg = f"There is not sandbox for job {job.name}"
            raise(RuntimeError(msg))
        snapshot = sandbox.snapshot
        if sandbox.snapshot is None:
            msg = f"There is not snapshot for sandbox {sandbox.id}."
            raise RuntimeError(msg)
        return self.create(snapshot)

    # TODO, call this, doesn't work?
    def destory(self, sandbox: DockerSandbox) -> None:
        """Stop and remove the Docker container."""
        self._executor.run(f"docker stop {sandbox.id}")
        self._executor.run(f"docker rm {sandbox.id}")

    def take_snapshot(self, sandbox: DockerSandbox) -> str:
        """Commit the Docker container and return image tag."""
        tag = f"river-sandbox:{str(uuid.uuid4()).replace('-', '')}"
        result = self._executor.run(f"docker commit {sandbox.id} {tag}")
        if not result.ok:
            msg = f"Task snapshot for docker sandbox failed, {result.stderr}"
            raise RuntimeError(msg)
        sandbox.snapshot = tag
        return tag
