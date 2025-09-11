import pytest
import unittest.mock
from unittest.mock import Mock, patch
from invoke.runners import Result
from sdk.river_sdk.sandbox.docker_sandbox import DockerSandbox, DockerSandboxManager
from sdk.river_sdk.sandbox.command_executor import CommandExecutor


class TestDockerSandbox:
    def setup_method(self):
        self.mock_executor = Mock(spec=CommandExecutor)
        self.sandbox = DockerSandbox("container_123", self.mock_executor)

    def test_init_sets_attributes(self):
        assert self.sandbox.id == "container_123"
        assert self.sandbox._executor is self.mock_executor

    def test_execute_basic_command(self):
        expected_result = Result(stdout="output", stderr="", command="", shell="", env={}, exited=0)
        self.mock_executor.run.return_value = expected_result

        result = self.sandbox.execute("ls", "/tmp")

        expected_cmd = "docker exec -w /tmp container_123 bash -c ls"
        self.mock_executor.run.assert_called_once_with(expected_cmd)
        assert result is expected_result

    def test_execute_with_env_vars(self):
        expected_result = Result(stdout="output", stderr="", command="", shell="", env={}, exited=0)
        self.mock_executor.run.return_value = expected_result

        env = {"VAR1": "value1", "VAR2": "value2"}
        result = self.sandbox.execute("echo $VAR1", "/home", env)

        expected_cmd = "docker exec -e VAR1=value1 -e VAR2=value2 -w /home container_123 bash -c 'echo $VAR1'"
        self.mock_executor.run.assert_called_once_with(expected_cmd)
        assert result is expected_result

    def test_execute_should_quote_inputs(self):
        """Test that inputs with special characters are properly quoted"""
        expected_result = Result(stdout="output", stderr="", command="", shell="", env={}, exited=0)
        self.mock_executor.run.return_value = expected_result

        # Test with special characters in paths and environment variables that need quoting
        result = self.sandbox.execute("echo hello", "/tmp with spaces", {"KEY": "value with spaces"})

        # shlex.quote() will quote strings with special characters
        expected_cmd = "docker exec -e 'KEY=value with spaces' -w '/tmp with spaces' container_123 bash -c 'echo hello'"
        self.mock_executor.run.assert_called_once_with(expected_cmd)
        assert result is expected_result

    def test_snapshot_property(self):
        # Test snapshot property getter and setter
        assert self.sandbox.snapshot is None

        self.sandbox.snapshot = "test_snapshot_tag"
        assert self.sandbox.snapshot == "test_snapshot_tag"


class TestDockerSandboxManager:
    def setup_method(self):
        self.image = "ubuntu:24.04"
        self.host = "localhost"

    @patch('sdk.river_sdk.sandbox.docker_sandbox.LocalCommandExecutor')
    def test_init_localhost(self, mock_local_executor):
        manager = DockerSandboxManager(self.host)

        assert manager._host == self.host
        mock_local_executor.assert_called_once()

    @patch('sdk.river_sdk.sandbox.docker_sandbox.RemoteCommandExecutor')
    def test_init_remote_host(self, mock_remote_executor):
        remote_host = "remote.example.com"
        manager = DockerSandboxManager(remote_host)

        assert manager._host == remote_host
        mock_remote_executor.assert_called_once_with(remote_host)

    def test_create(self):
        manager = DockerSandboxManager()
        mock_executor = Mock()
        manager._executor = mock_executor

        # Mock successful docker run
        mock_result = Mock()
        mock_result.stdout = "container_id_123\n"
        mock_executor.run.return_value = mock_result

        result = manager.create(self.image)

        expected_calls = [
            unittest.mock.call(f"docker run -d {self.image} tail -f /dev/null"),
            unittest.mock.call("docker exec container_id_123 mkdir -p /river")
        ]
        mock_executor.run.assert_has_calls(expected_calls)
        assert isinstance(result, DockerSandbox)
        assert result.id == "container_id_123"

    def test_destory(self):
        manager = DockerSandboxManager()
        mock_executor = Mock()
        manager._executor = mock_executor

        sandbox = DockerSandbox("container_123", Mock())
        manager.destory(sandbox)

        # Currently the destory method is a no-op (commented out), so no calls expected
        mock_executor.run.assert_not_called()

    @patch('uuid.uuid4')
    def test_take_snapshot_success(self, mock_uuid):
        manager = DockerSandboxManager()
        mock_executor = Mock()
        manager._executor = mock_executor

        # Mock UUID generation
        mock_uuid_obj = Mock()
        mock_uuid_obj.__str__ = Mock(return_value="12345678-1234-1234-1234-123456789012")
        mock_uuid.return_value = mock_uuid_obj

        # Mock successful docker commit
        mock_result = Mock()
        mock_result.ok = True
        mock_result.stdout = "sha256:abcdef123456\n"
        mock_executor.run.return_value = mock_result

        sandbox = DockerSandbox("container_123", Mock())
        result = manager.take_snapshot(sandbox, "test-fingerprint-123")

        expected_tag = "river-sandbox:test-fingerprint-123"
        mock_executor.run.assert_called_once_with(f"docker commit container_123 {expected_tag}")
        assert result == expected_tag

    @patch('uuid.uuid4')
    def test_take_snapshot_failure(self, mock_uuid):
        manager = DockerSandboxManager()
        mock_executor = Mock()
        manager._executor = mock_executor

        # Mock UUID generation
        mock_uuid_obj = Mock()
        mock_uuid_obj.__str__ = Mock(return_value="12345678-1234-1234-1234-123456789012")
        mock_uuid.return_value = mock_uuid_obj

        # Mock failed docker commit
        mock_result = Mock()
        mock_result.ok = False
        mock_result.stderr = "Docker commit failed"
        mock_executor.run.return_value = mock_result

        sandbox = DockerSandbox("container_123", Mock())

        with pytest.raises(RuntimeError, match="Task snapshot for docker sandbox failed, Docker commit failed"):
            manager.take_snapshot(sandbox, "test-fingerprint-failure")

    def test_fork_success(self):
        manager = DockerSandboxManager()
        mock_executor = Mock()
        manager._executor = mock_executor

        # Mock successful docker run for fork
        mock_result = Mock()
        mock_result.stdout = "forked_container_456\n"
        mock_executor.run.return_value = mock_result

        # Create sandbox with snapshot
        sandbox = DockerSandbox("container_123", Mock())
        sandbox.snapshot = "test_snapshot_tag"
        
        # Create mock job with sandbox
        mock_job = Mock()
        mock_job.sandbox = sandbox
        
        result = manager.fork(mock_job)
        
        expected_calls = [
            unittest.mock.call("docker run -d test_snapshot_tag tail -f /dev/null"),
            unittest.mock.call("docker exec forked_container_456 mkdir -p /river")
        ]
        mock_executor.run.assert_has_calls(expected_calls)
        assert isinstance(result, DockerSandbox)
        assert result.id == "forked_container_456"

    def test_fork_failure_no_snapshot(self):
        manager = DockerSandboxManager()

        # Create sandbox without snapshot
        sandbox = DockerSandbox("container_123", Mock())
        
        # Create mock job with sandbox
        mock_job = Mock()
        mock_job.sandbox = sandbox

        with pytest.raises(RuntimeError, match="There is not snapshot for sandbox container_123."):
            manager.fork(mock_job)

    def test_creator_returns_callable(self):
        manager = DockerSandboxManager()
        image = "ubuntu:24.04"
        
        creator_func = manager.creator(image)
        
        # Verify it returns a callable
        assert callable(creator_func)

    def test_creator_callable_creates_sandbox(self):
        manager = DockerSandboxManager()
        mock_executor = Mock()
        manager._executor = mock_executor
        image = "ubuntu:24.04"

        # Mock successful docker run
        mock_result = Mock()
        mock_result.stdout = "created_container_789\n"
        mock_executor.run.return_value = mock_result

        creator_func = manager.creator(image)
        result = creator_func()

        # Verify the creator function calls create with the correct image
        expected_calls = [
            unittest.mock.call(f"docker run -d {image} tail -f /dev/null"),
            unittest.mock.call("docker exec created_container_789 mkdir -p /river")
        ]
        mock_executor.run.assert_has_calls(expected_calls)
        assert isinstance(result, DockerSandbox)
        assert result.id == "created_container_789"
