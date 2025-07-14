import uuid

from typing import Optional
from sdk.src.sandbox.command_executor import LocalCommandExecutor, RemoteCommandExecutor
from invoke.runners import Result
from sdk.src.sandbox.base_sandbox import BaseSandbox


class DockerSandbox(BaseSandbox):
    def __init__(self, image: str, host: str = "localhost"):
        super().__init__()
        self.image = image
        self._host = host
        self._executor = LocalCommandExecutor() if host == "localhost" else RemoteCommandExecutor(host)
    
    def _create_impl(self) -> str:
        """Start a Docker container and return its ID."""
        result = self._executor.run(f"docker run -d {self.image} sleep infinity")
        return result.stdout.strip()

    def _destory_impl(self, sandbox_id: str) -> None:
        """Stop and remove the Docker container."""
        self._executor.run(f"docker stop {sandbox_id}")
        self._executor.run(f"docker rm {sandbox_id}")

    def _take_snapshot_impl(self, sandbox_id: str) -> str:
        tag = f"river-sandbox:{str(uuid.uuid4()).replace('-', '')}"
        result = self._executor.run(f"docker commit {sandbox_id} {tag}")
        if not result.ok:
            msg = f"Task snapshot for docker sandbox failed, {result.stderr}"
            raise RuntimeError(msg)
        return tag

    def execute(
        self,
        command: str,
        cwd: str,
        env: Optional[dict[str, str]] = None
    ) -> Result:
        """Generate docker exec command"""
        if not self.id:
            raise RuntimeError("Docker sandbox not started")
        
        docker_cmd = f"docker exec"
        
        # Add environment variables
        if env:
            for key, value in env.items():
                docker_cmd += f" -e {key}={value}"
        
        docker_cmd += f" -w {cwd}"
        docker_cmd += f" {self.id} {command}"
        
        return self._executor.run(docker_cmd)
