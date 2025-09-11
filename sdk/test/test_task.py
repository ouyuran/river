import pytest
from unittest.mock import Mock, patch
from sdk.river_sdk.task import TaskExecutionError, bash
from sdk.river_sdk.sandbox.base_sandbox import BaseSandbox


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

    @pytest.fixture
    def mock_job_no_sandbox(self):
        """Fixture for job without sandbox."""
        mock_job = Mock()
        mock_job.sandbox = None
        return mock_job

    @pytest.fixture  
    def mock_job_with_sandbox(self):
        """Fixture for job with sandbox."""
        mock_sandbox = Mock(spec=BaseSandbox)
        mock_job = Mock()
        mock_job.sandbox = mock_sandbox
        return mock_job, mock_sandbox

    @pytest.fixture
    def mock_failed_result(self):
        """Fixture for failed command result."""
        def _create_result(stdout="", stderr="", exit_code=1):
            mock_result = Mock()
            mock_result.stdout = stdout
            mock_result.stderr = stderr
            mock_result.exited = exit_code
            mock_result.ok = False
            return mock_result
        return _create_result

    @patch('sdk.river_sdk.task.get_current_job')
    def test_bash_success_with_local_executor(self, mock_get_current_job, mock_job_no_sandbox):
        """Test bash function success case with LocalCommandExecutor."""
        mock_get_current_job.return_value = mock_job_no_sandbox
        
        with patch('sdk.river_sdk.task.LocalCommandExecutor') as mock_executor_class:
            mock_executor = Mock()
            mock_executor_class.return_value = mock_executor
            
            bash("echo test", cwd="/tmp", env={"VAR": "value"})
            
            mock_executor.run.assert_called_once_with(
                command="echo test",
                cwd="/tmp",
                env={"VAR": "value"}
            )

    @patch('sdk.river_sdk.task.get_current_job')
    def test_bash_success_with_sandbox(self, mock_get_current_job, mock_job_with_sandbox):
        """Test bash function success case with sandbox executor."""
        mock_job, mock_sandbox = mock_job_with_sandbox
        mock_get_current_job.return_value = mock_job
        
        bash("ls", cwd="/home", env={"PATH": "/usr/bin"})
        
        mock_sandbox.execute.assert_called_once_with(
            command="ls",
            cwd="/home",
            env={"PATH": "/usr/bin"}
        )

    @patch('sdk.river_sdk.task.get_current_job')
    def test_bash_failure_with_local_executor_raises_error(self, mock_get_current_job, 
                                                          mock_job_no_sandbox, mock_failed_result):
        """Test bash function failure case with LocalCommandExecutor raises TaskExecutionError."""
        mock_get_current_job.return_value = mock_job_no_sandbox
        failed_result = mock_failed_result(stderr="command not found", exit_code=127)
        
        with patch('sdk.river_sdk.task.LocalCommandExecutor') as mock_executor_class:
            mock_executor = Mock()
            mock_executor.run.return_value = failed_result
            mock_executor_class.return_value = mock_executor
            
            with pytest.raises(TaskExecutionError) as exc_info:
                bash("invalid_cmd")
            
            error = exc_info.value
            assert error.command == "invalid_cmd"
            assert error.stdout == ""
            assert error.stderr == "command not found"
            assert error.exit_code == 127

    @patch('sdk.river_sdk.task.get_current_job')
    def test_bash_failure_with_sandbox_raises_error(self, mock_get_current_job, 
                                                   mock_job_with_sandbox, mock_failed_result):
        """Test bash function failure case with sandbox raises TaskExecutionError."""
        mock_job, mock_sandbox = mock_job_with_sandbox
        mock_get_current_job.return_value = mock_job
        failed_result = mock_failed_result(stdout="partial output", stderr="permission denied", exit_code=1)
        mock_sandbox.execute.return_value = failed_result
        
        with pytest.raises(TaskExecutionError) as exc_info:
            bash("rm /protected")
        
        error = exc_info.value
        assert error.command == "rm /protected"
        assert error.stdout == "partial output"
        assert error.stderr == "permission denied"
        assert error.exit_code == 1
