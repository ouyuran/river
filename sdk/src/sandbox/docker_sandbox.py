import uuid

from fabric import Connection
from typing import Optional
from sdk.src.sandbox.command_executor import CommandExecutor, LocalCommandExecutor, RemoteCommandExecutor
from invoke.runners import Result
from sdk.src.sandbox.base_sandbox import BaseSandbox, BaseSandboxManager


class DockerSandbox(BaseSandbox):
    def __init__(self, id: str, executor: CommandExecutor):
        super().__init__(id)
        self._executor: CommandExecutor = executor
        self._connection: Optional[Connection] = None

    def execute(
        self,
        command: str,
        cwd: str,
        env: Optional[dict[str, str]] = None
    ) -> Result:
        """Generate docker exec command"""
        docker_cmd = f"docker exec"
        
        # Add environment variables
        if env:
            for key, value in env.items():
                docker_cmd += f" -e {key}={value}"
        
        docker_cmd += f" -w {cwd}"
        docker_cmd += f" {self.id} {command}"
        
        return self._executor.run(docker_cmd)
    

class DockerSandboxManager(BaseSandboxManager):
    def __init__(self, image: str, host: str = "localhost"):
        super().__init__()
        self.image = image
        self._host = host
        self._executor = self._create_executor(host)
    
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
        return tag
