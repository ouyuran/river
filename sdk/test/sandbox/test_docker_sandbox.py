import pytest
import unittest.mock
from unittest.mock import Mock, patch
from invoke.runners import Result
from sdk.src.sandbox.docker_sandbox import DockerSandbox


class TestDockerSandbox:
    def setup_method(self):
        self.image = "ubuntu:24.04"
        self.host = "localhost"

    @patch('sdk.src.sandbox.docker_sandbox.LocalCommandExecutor')
    def test_init_localhost(self, mock_local_executor):
        sandbox = DockerSandbox(self.image, self.host)
        
        assert sandbox.image == self.image
        assert sandbox._host == self.host
        mock_local_executor.assert_called_once()

    @patch('sdk.src.sandbox.docker_sandbox.RemoteCommandExecutor')
    def test_init_remote_host(self, mock_remote_executor):
        remote_host = "remote.example.com"
        sandbox = DockerSandbox(self.image, remote_host)
        
        assert sandbox.image == self.image
        assert sandbox._host == remote_host
        mock_remote_executor.assert_called_once_with(remote_host)

    def test_create_impl(self):
        sandbox = DockerSandbox(self.image)
        mock_executor = Mock()
        sandbox._executor = mock_executor
        
        # Mock successful docker run
        mock_result = Mock()
        mock_result.stdout = "container_id_123\n"
        mock_executor.run.return_value = mock_result
        
        result = sandbox._create_impl()
        
        mock_executor.run.assert_called_once_with(f"docker run -d {self.image} sleep infinity")
        assert result == "container_id_123"

    def test_destory_impl(self):
        sandbox = DockerSandbox(self.image)
        mock_executor = Mock()
        sandbox._executor = mock_executor
        
        sandbox_id = "container_123"
        sandbox._destory_impl(sandbox_id)
        
        expected_calls = [
            unittest.mock.call(f"docker stop {sandbox_id}"),
            unittest.mock.call(f"docker rm {sandbox_id}")
        ]
        mock_executor.run.assert_has_calls(expected_calls)

    @patch('uuid.uuid4')
    def test_take_snapshot_impl_success(self, mock_uuid):
        sandbox = DockerSandbox(self.image)
        mock_executor = Mock()
        sandbox._executor = mock_executor
        
        # Mock UUID generation
        mock_uuid_obj = Mock()
        mock_uuid_obj.__str__ = Mock(return_value="12345678-1234-1234-1234-123456789012")
        mock_uuid.return_value = mock_uuid_obj
        
        # Mock successful docker commit
        mock_result = Mock()
        mock_result.ok = True
        mock_result.stdout = "sha256:abcdef123456\n"
        mock_executor.run.return_value = mock_result
        
        sandbox_id = "container_123"
        result = sandbox._take_snapshot_impl(sandbox_id)
        
        expected_tag = "river-sandbox:12345678123412341234123456789012"  # UUID without dashes (full 32 chars)
        mock_executor.run.assert_called_once_with(f"docker commit {sandbox_id} {expected_tag}")
        assert result == expected_tag

    @patch('uuid.uuid4')
    def test_take_snapshot_impl_failure(self, mock_uuid):
        sandbox = DockerSandbox(self.image)
        mock_executor = Mock()
        sandbox._executor = mock_executor
        
        # Mock UUID generation
        mock_uuid_obj = Mock()
        mock_uuid_obj.__str__ = Mock(return_value="12345678-1234-1234-1234-123456789012")
        mock_uuid.return_value = mock_uuid_obj
        
        # Mock failed docker commit
        mock_result = Mock()
        mock_result.ok = False
        mock_result.stderr = "Docker commit failed"
        mock_executor.run.return_value = mock_result
        
        sandbox_id = "container_123"
        
        with pytest.raises(RuntimeError, match="Task snapshot for docker sandbox failed, Docker commit failed"):
            sandbox._take_snapshot_impl(sandbox_id)

    def test_execute_basic_command(self):
        sandbox = DockerSandbox(self.image)
        mock_executor = Mock()
        sandbox._executor = mock_executor
        sandbox.id = "container_123"
        
        expected_result = Result(stdout="output", stderr="", command="", shell="", env={}, exited=0)
        mock_executor.run.return_value = expected_result
        
        result = sandbox.execute("ls", "/tmp")
        
        expected_cmd = "docker exec -w /tmp container_123 ls"
        mock_executor.run.assert_called_once_with(expected_cmd)
        assert result is expected_result

    def test_execute_with_env_vars(self):
        sandbox = DockerSandbox(self.image)
        mock_executor = Mock()
        sandbox._executor = mock_executor
        sandbox.id = "container_123"
        
        expected_result = Result(stdout="output", stderr="", command="", shell="", env={}, exited=0)
        mock_executor.run.return_value = expected_result
        
        env = {"VAR1": "value1", "VAR2": "value2"}
        result = sandbox.execute("echo $VAR1", "/home", env)
        
        expected_cmd = "docker exec -e VAR1=value1 -e VAR2=value2 -w /home container_123 echo $VAR1"
        mock_executor.run.assert_called_once_with(expected_cmd)
        assert result is expected_result

    def test_execute_without_sandbox_id_raises_error(self):
        sandbox = DockerSandbox(self.image)
        sandbox.id = ""  # No sandbox started
        
        with pytest.raises(RuntimeError, match="Docker sandbox not started"):
            sandbox.execute("ls", "/tmp")