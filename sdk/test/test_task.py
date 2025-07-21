import pytest
from unittest.mock import Mock, patch
from sdk.src.task import TaskExecutionError, bash
from sdk.src.sandbox.base_sandbox import BaseSandbox


class TestTaskExecutionError:
    """Test cases for TaskExecutionError custom exception."""

    def test_task_execution_error_init_with_all_params(self):
        """Test TaskExecutionError initialization with all parameters."""
        command = "ls -invalid"
        stdout = "some output"
        stderr = "invalid option error"
        exit_code = 2
        
        error = TaskExecutionError(command, stdout, stderr, exit_code)
        
        assert error.command == command
        assert error.stdout == stdout
        assert error.stderr == stderr
        assert error.exit_code == exit_code
        
        expected_msg = f"Command '{command}' failed with exit code {exit_code}\nstderr: {stderr}\nstdout: {stdout}"
        assert str(error) == expected_msg

    def test_task_execution_error_init_with_minimal_params(self):
        """Test TaskExecutionError initialization with minimal parameters."""
        command = "test command"
        
        error = TaskExecutionError(command)
        
        assert error.command == command
        assert error.stdout == ""
        assert error.stderr == ""
        assert error.exit_code == 0
        
        expected_msg = f"Command '{command}' failed with exit code 0"
        assert str(error) == expected_msg

    def test_task_execution_error_with_stderr_only(self):
        """Test TaskExecutionError with only stderr."""
        command = "failing command"
        stderr = "command not found"
        exit_code = 127
        
        error = TaskExecutionError(command, stderr=stderr, exit_code=exit_code)
        
        expected_msg = f"Command '{command}' failed with exit code {exit_code}\nstderr: {stderr}"
        assert str(error) == expected_msg

    def test_task_execution_error_with_stdout_only(self):
        """Test TaskExecutionError with only stdout."""
        command = "echo test"
        stdout = "test output"
        exit_code = 1
        
        error = TaskExecutionError(command, stdout=stdout, exit_code=exit_code)
        
        expected_msg = f"Command '{command}' failed with exit code {exit_code}\nstdout: {stdout}"
        assert str(error) == expected_msg


class TestBashFunction:
    """Test cases for the bash function."""

    @patch('sdk.src.task.job_context')
    def test_bash_success_with_local_executor(self, mock_job_context):
        """Test bash function success case with LocalCommandExecutor."""
        # Mock job context with no sandbox
        mock_job = Mock()
        mock_job.sandbox = None
        mock_job_context.get.return_value = mock_job
        
        with patch('sdk.src.task.LocalCommandExecutor') as mock_executor_class:
            mock_executor = Mock()
            mock_executor_class.return_value = mock_executor
            
            bash("echo test", cwd="/tmp", env={"VAR": "value"})
            
            mock_executor.run.assert_called_once_with(
                command="echo test",
                cwd="/tmp",
                env={"VAR": "value"}
            )

    @patch('sdk.src.task.job_context')
    def test_bash_success_with_sandbox(self, mock_job_context):
        """Test bash function success case with sandbox executor."""
        # Mock job context with sandbox
        mock_sandbox = Mock(spec=BaseSandbox)
        mock_job = Mock()
        mock_job.sandbox = mock_sandbox
        mock_job_context.get.return_value = mock_job
        
        bash("ls", cwd="/home", env={"PATH": "/usr/bin"})
        
        mock_sandbox.execute.assert_called_once_with(
            command="ls",
            cwd="/home",
            env={"PATH": "/usr/bin"}
        )

    @patch('sdk.src.task.job_context')
    def test_bash_failure_with_local_executor_raises_error(self, mock_job_context):
        """Test bash function failure case with LocalCommandExecutor raises TaskExecutionError."""
        # Mock job context with no sandbox
        mock_job = Mock()
        mock_job.sandbox = None
        mock_job_context.get.return_value = mock_job
        
        # Mock failed result
        mock_result = Mock()
        mock_result.stdout = ""
        mock_result.stderr = "command not found"
        mock_result.exited = 127
        mock_result.ok = False
        
        with patch('sdk.src.task.LocalCommandExecutor') as mock_executor_class:
            mock_executor = Mock()
            mock_executor.run.return_value = mock_result
            mock_executor_class.return_value = mock_executor
            
            with pytest.raises(TaskExecutionError) as exc_info:
                bash("invalid_cmd")
            
            error = exc_info.value
            assert error.command == "invalid_cmd"
            assert error.stdout == ""
            assert error.stderr == "command not found"
            assert error.exit_code == 127

    @patch('sdk.src.task.job_context')
    def test_bash_failure_with_sandbox_raises_error(self, mock_job_context):
        """Test bash function failure case with sandbox raises TaskExecutionError."""
        # Mock job context with sandbox
        mock_sandbox = Mock(spec=BaseSandbox)
        mock_job = Mock()
        mock_job.sandbox = mock_sandbox
        mock_job_context.get.return_value = mock_job
        
        # Mock failed result
        mock_result = Mock()
        mock_result.stdout = "partial output"
        mock_result.stderr = "permission denied"
        mock_result.exited = 1
        mock_result.ok = False
        mock_sandbox.execute.return_value = mock_result
        
        with pytest.raises(TaskExecutionError) as exc_info:
            bash("rm /protected")
        
        error = exc_info.value
        assert error.command == "rm /protected"
        assert error.stdout == "partial output"
        assert error.stderr == "permission denied"
        assert error.exit_code == 1
