from typing import Dict, Optional
import uuid
from river_sdk.job import get_current_job
from river_sdk.sandbox.command_executor import LocalCommandExecutor
from river_common.status import TaskStatus
from river_common.shared import Status


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


def _export_task_status(task_id: str, task_name: str, parent_id: str, status: Status, exception: Optional[Exception] = None):
    """Export task status if needed"""
    task_status = TaskStatus(
        id=task_id,
        name=task_name,
        parent_id=parent_id,
        status=status
    )
    
    if status == Status.FAILED and exception:
        task_status.set_failed(exception)
    
    task_status.export()


def bash(command: str, cwd: Optional[str] = None, env: Optional[Dict[str, str]] = None, task_name: Optional[str] = None):
    job = get_current_job()
    sandbox = job.sandbox
    
    # Create task identifiers
    task_id = str(uuid.uuid4())
    if task_name is None:
        task_name = f"bash: {command[:50]}..." if len(command) > 50 else f"bash: {command}"
    
    # Export initial status
    _export_task_status(task_id, task_name, job.id, Status.RUNNING)
    
    try:
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
            error = TaskExecutionError(
                command=command,
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.exited
            )
            raise error
        
        _export_task_status(task_id, task_name, job.id, Status.SUCCESS)
        return result

    except Exception as e:
        _export_task_status(task_id, task_name, job.id, Status.FAILED, e)
        raise
