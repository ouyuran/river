import pytest
import sys
import os
from unittest.mock import Mock, patch
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from runner.src.remote_executor import RemoteExecutor

class TestRemoteExecutor:
    
    @pytest.fixture
    def mock_connection_setup(self):
        """Setup mock connection for fabric Connection"""
        with patch('runner.src.remote_executor.Connection') as mock_connection:
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
        result.return_code = 0
        result.stdout = "remote output"
        result.stderr = "remote error"
        return result
    
    def test_init_stores_connection_params(self):
        """Test that RemoteExecutor stores connection parameters"""
        executor = RemoteExecutor('example.com', user='testuser', key_filename='/path/to/key', password='secret', port=2222)
        
        assert executor.host == 'example.com'
        assert executor.user == 'testuser' 
        assert executor.port == 2222
        assert executor.connect_kwargs == {
            'key_filename': '/path/to/key',
            'password': 'secret'
        }
    
    def test_execute_task_calls_fabric_run(self, mock_connection_setup, mock_result):
        """Test that execute_task correctly creates connection and calls fabric run method"""
        mock_connection, mock_conn_instance = mock_connection_setup
        mock_conn_instance.run.return_value = mock_result
        
        executor = RemoteExecutor('example.com', user='testuser', port=2222)
        task = {
            'command': 'ls -la',
            'env': {'REMOTE_KEY': 'remote_value'},
            'cwd': '/home/user'
        }
        
        return_code, stdout, stderr = executor.execute_task(task)
        
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
        
        assert return_code == 0
        assert stdout == "remote output"
        assert stderr == "remote error"
    
    @patch('runner.src.remote_executor.BaseExecutor.safe_env')
    def test_execute_task_calls_safe_env(self, mock_safe_env, mock_connection_setup):
        """Test that execute_task calls safe_env to validate environment"""
        mock_connection, mock_conn_instance = mock_connection_setup
        mock_result = Mock()
        mock_conn_instance.run.return_value = mock_result
        mock_safe_env.return_value = {'SAFE_KEY': '123'}
        
        executor = RemoteExecutor('example.com')
        task = {
            'command': 'test',
            'env': {'KEY': 123},  # Non-string value
            'cwd': '/tmp'
        }
        
        executor.execute_task(task)
        
        # Verify safe_env was called
        mock_safe_env.assert_called_once_with({'KEY': 123})
        
        # Verify the safe env was passed to fabric
        mock_conn_instance.run.assert_called_once_with(
            'test',
            env={'SAFE_KEY': '123'},
            hide=True,
            warn=True
        )
    
    def test_execute_task_default_cwd(self, mock_connection_setup):
        """Test that execute_task uses '~' as default cwd"""
        mock_connection, mock_conn_instance = mock_connection_setup
        mock_result = Mock()
        mock_conn_instance.run.return_value = mock_result
        
        executor = RemoteExecutor('example.com')
        task = {
            'command': 'test',
            'env': {}
        }
        
        executor.execute_task(task)
        
        mock_conn_instance.cd.assert_called_once_with('~')
    
    def test_execute_task_exception_handling(self):
        """Test that exceptions are handled properly"""
        with patch('runner.src.remote_executor.Connection') as mock_connection:
            mock_connection.side_effect = Exception("Connection failed")
            
            executor = RemoteExecutor('example.com')
            task = {
                'command': 'test',
                'env': {},
                'cwd': '/tmp'
            }
            
            return_code, stdout, stderr = executor.execute_task(task)
            
            assert return_code == 1
            assert stdout == ""
            assert "Connection failed" in stderr
