from __future__ import annotations

import uuid
import shlex
import base64
import cloudpickle

from fabric import Connection
from functools import partial
from typing import Callable, Optional, TYPE_CHECKING
from river_sdk.sandbox.command_executor import CommandExecutor, LocalCommandExecutor, RemoteCommandExecutor
from invoke.runners import Result
from river_sdk.sandbox.base_sandbox import BaseSandbox, BaseSandboxManager
from river_common.status import JobStatus

if TYPE_CHECKING:
    from river_sdk.job import Job, JobResult

RIVER_ROOT = "/river"
JOB_STATUS_FILE = f"{RIVER_ROOT}/job_status"


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
        # Add environment variables (with safe escaping)
        if env:
            for key, value in env.items():
                env_pair = f"{key}={value}"
                safe_env_pair = shlex.quote(env_pair)
                docker_cmd += f" -e {safe_env_pair}"
        
        # Add working directory (with safe escaping)
        safe_cwd = shlex.quote(cwd if cwd is not None else '/')
        docker_cmd += f" -w {safe_cwd}"
        
        # Add container ID and command (with safe escaping)
        safe_container_id = shlex.quote(self.id)
        safe_command = shlex.quote(command)
        docker_cmd += f" {safe_container_id} bash -c {safe_command}"
        
        return self._executor.run(docker_cmd)
    
    @property
    def snapshot(self) -> Optional[str]:
        return self._snapshot
    
    @snapshot.setter
    def snapshot(self, tag: str):
        self._snapshot = tag
    

class DockerSandboxManager(BaseSandboxManager):
    def __init__(self, host: str = "localhost"):
        super().__init__()
        self._host: str = host
        self._executor: CommandExecutor = self._create_executor(host)
    
    def _create_executor(self,host: str) -> CommandExecutor:
        return LocalCommandExecutor() if host == "localhost" else RemoteCommandExecutor(host)
    
    def creator(self, image: str) -> Callable[[], BaseSandbox]:
        return partial(self.create, image)

    def create(self, image: str) -> DockerSandbox:
        """Start a Docker container.
        
        Args:
            image: docker image.

        Returns:
            DockerSandBox: The representation of the started container.
        """
        result = self._executor.run(f"docker run -d {image} tail -f /dev/null")
        container_id = result.stdout.strip()
        self._executor.run(f"docker exec {container_id} mkdir -p {RIVER_ROOT}")
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

    def destory(self, sandbox: DockerSandbox) -> None:
        """Stop and remove the Docker container."""
        # self._executor.run(f"docker stop -t 0 {sandbox.id}")
        # self._executor.run(f"docker rm {sandbox.id}")

    def _get_tag(self, fingerprint:str) -> str:
        return f"river-sandbox:{fingerprint}"

    def take_snapshot(self, sandbox: DockerSandbox, fingerprint: str) -> str:
        """Commit the Docker container and return image tag."""
        tag = self._get_tag(fingerprint)
        result = self._executor.run(f"docker commit {sandbox.id} {tag}")
        if not result.ok:
            msg = f"Task snapshot for docker sandbox failed, {result.stderr}"
            raise RuntimeError(msg)
        sandbox.snapshot = tag
        return tag
    
    def snapshot_exists(self, fingerprint: str) -> bool:
        tag = self._get_tag(fingerprint)
        result = self._executor.run(" ".join([
            "docker images --format",
            "'{{.Repository}}:{{.Tag}}'",
            "|",
            f"grep -w '{tag}'"
        ]))
        return result.ok
    
    def set_job_result_to_sandbox(self, sandbox: DockerSandbox, job_result: JobResult) -> None:
        result_binary = cloudpickle.dumps(job_result)
        
        encoded_result_binary = base64.b64encode(result_binary).decode()
        safe_container_id = shlex.quote(sandbox.id)
        safe_job_status_file = shlex.quote(JOB_STATUS_FILE)
        
        command = f"docker exec {safe_container_id} sh -c 'echo {encoded_result_binary} > {safe_job_status_file}'"
        print(command)
        result = self._executor.run(command)
        print(result)
        if not result.ok:
            msg = f"Cannot set job result: {result.stderr}"
            raise RuntimeError(msg)

    def get_job_result_from_snapshot(self, fingerprint: str) -> JobResult:
        tag = self._get_tag(fingerprint)
        result = self._executor.run(f"docker run {tag} cat {JOB_STATUS_FILE}")
        if result.ok:
            encoded_result_binary = result.stdout.strip().encode()
            result_binary = base64.b64decode(encoded_result_binary)
            return cloudpickle.loads(result_binary)
        else:
            msg = f"Cannot get cached job result from {fingerprint=}, {result.stderr}"
            raise RuntimeError(msg)
