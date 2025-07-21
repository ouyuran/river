from typing import Dict, Optional
from sdk.src.job import job_context
from sdk.src.sandbox.command_executor import LocalCommandExecutor


class TaskExecutionError(Exception):
    """Custom exception raised when a task command execution fails."""
    
    def __init__(self, command: str, stdout: str = "", stderr: str = "", exit_code: int = 0):
        self.command = command
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code
        
        error_msg = f"Command '{command}' failed with exit code {exit_code}"
        if stderr:
            error_msg += f"\nstderr: {stderr}"
        if stdout:
            error_msg += f"\nstdout: {stdout}"
            
        super().__init__(error_msg)


def bash(command: str, cwd: Optional[str] = None, env: Optional[Dict[str, str]] = None):
    job = job_context.get()
    sandbox = job.sandbox
    
    if sandbox is None:
        result = LocalCommandExecutor().run(
            command=command,
            cwd=cwd,
            env=env
        )
    else:
        result = sandbox.execute(
            command=command,
            cwd=cwd,
            env=env
        )

    if not result.ok:
        raise TaskExecutionError(
            command=command,
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.exited
        )
    
    return result
