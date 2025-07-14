import pytest

from unittest.mock import Mock, patch
from sdk.src.sandbox.command_executor import LocalCommandExecutor, RemoteCommandExecutor


class TestLocalCommandExecutor:
    
    @pytest.fixture
    def mock_connection_setup(self):
        """Setup mock connection for fabric Connection"""
        with patch('sdk.src.sandbox.command_executor.Connection') as mock_connection:
            mock_conn_instance = Mock()
            mock_connection.return_value.__enter__ = Mock(return_value=mock_conn_instance)
            mock_connection.return_value.__exit__ = Mock(return_value=None)
            mock_conn_instance.cd.return_value.__enter__ = Mock(return_value=mock_conn_instance)
            mock_conn_instance.cd.return_value.__exit__ = Mock(return_value=None)
            
            yield mock_connection, mock_conn_instance
    
    @pytest.fixture
    def mock_result(self):
        """Setup mock result for fabric operations"""
        result = Mock()
        result.exited = 0
        result.stdout = "test output"
        result.stderr = "test error"
        return result
    
    def test_run_calls_fabric_local(self, mock_connection_setup, mock_result):
        """Test that run correctly creates connection and calls fabric local method"""
        mock_connection, mock_conn_instance = mock_connection_setup
        mock_conn_instance.local.return_value = mock_result
        
        executor = LocalCommandExecutor()
        result = executor.run('echo "hello"', cwd='/tmp', env={'KEY': 'value'})
        
        # Verify connection was created to localhost
        mock_connection.assert_called_once_with('localhost')
        
        # Verify fabric local was called correctly
        mock_conn_instance.cd.assert_called_once_with('/tmp')
        mock_conn_instance.local.assert_called_once_with(
            'echo "hello"',
            env={'KEY': 'value'},
            hide=True,
            warn=True
        )
        
        assert result == mock_result
    
    def test_run_default_cwd(self, mock_connection_setup, mock_result):
        """Test that run uses '.' as default cwd"""
        mock_connection, mock_conn_instance = mock_connection_setup
        mock_conn_instance.local.return_value = mock_result
        
        executor = LocalCommandExecutor()
        executor.run('test')
        
        mock_conn_instance.cd.assert_called_once_with('.')
    
    def test_run_none_result(self, mock_connection_setup):
        """Test handling when fabric local returns None"""
        mock_connection, mock_conn_instance = mock_connection_setup
        mock_conn_instance.local.return_value = None
        
        executor = LocalCommandExecutor()
        result = executor.run('test', cwd='/tmp')
        
        assert result.exited == 1
        assert result.stderr == "Local run returns None"


class TestRemoteCommandExecutor:
    
    @pytest.fixture
    def mock_connection_setup(self):
        """Setup mock connection for fabric Connection"""
        with patch('sdk.src.sandbox.command_executor.Connection') as mock_connection:
            mock_conn_instance = Mock()
            mock_connection.return_value.__enter__ = Mock(return_value=mock_conn_instance)
            mock_connection.return_value.__exit__ = Mock(return_value=None)
            mock_conn_instance.cd.return_value.__enter__ = Mock(return_value=mock_conn_instance)
            mock_conn_instance.cd.return_value.__exit__ = Mock(return_value=None)
            
            yield mock_connection, mock_conn_instance
    
    @pytest.fixture
    def mock_result(self):
        """Setup mock result for fabric operations"""
        result = Mock()
        result.exited = 0
        result.stdout = "remote output"
        result.stderr = "remote error"
        return result
    
    def test_init_stores_connection_params(self):
        """Test that RemoteCommandExecutor stores connection parameters"""
        executor = RemoteCommandExecutor('example.com', user='testuser', key_filename='/path/to/key', password='secret', port=2222)
        
        assert executor.host == 'example.com'
        assert executor.user == 'testuser' 
        assert executor.port == 2222
        assert executor.connect_kwargs == {
            'key_filename': '/path/to/key',
            'password': 'secret'
        }
    
    def test_run_calls_fabric_run(self, mock_connection_setup, mock_result):
        """Test that run correctly creates connection and calls fabric run method"""
        mock_connection, mock_conn_instance = mock_connection_setup
        mock_conn_instance.run.return_value = mock_result
        
        executor = RemoteCommandExecutor('example.com', user='testuser', port=2222)
        result = executor.run('ls -la', cwd='/home/user', env={'REMOTE_KEY': 'remote_value'})
        
        # Verify connection was created with correct parameters
        mock_connection.assert_called_once_with(
            host='example.com',
            user='testuser',
            port=2222,
            connect_kwargs={}
        )
        
        # Verify fabric run was called correctly
        mock_conn_instance.cd.assert_called_once_with('/home/user')
        mock_conn_instance.run.assert_called_once_with(
            'ls -la',
            env={'REMOTE_KEY': 'remote_value'},
            hide=True,
            warn=True
        )
        
        assert result == mock_result
    
    def test_run_default_cwd(self, mock_connection_setup, mock_result):
        """Test that run uses '.' as default cwd"""
        mock_connection, mock_conn_instance = mock_connection_setup
        mock_conn_instance.run.return_value = mock_result
        
        executor = RemoteCommandExecutor('example.com')
        executor.run('test')
        
        mock_conn_instance.cd.assert_called_once_with('.')