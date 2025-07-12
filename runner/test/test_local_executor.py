import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from runner.src.local_executor import LocalExecutor

class TestLocalExecutor:
    
    @pytest.fixture
    def mock_connection_setup(self):
        """Setup mock connection for fabric Connection"""
        with patch('runner.src.local_executor.Connection') as mock_connection:
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
        result.stdout = "test output"
        result.stderr = "test error"
        return result
    
    def test_execute_task_calls_fabric_local(self, mock_connection_setup, mock_result):
        """Test that execute_task correctly creates connection and calls fabric local method"""
        mock_connection, mock_conn_instance = mock_connection_setup
        mock_conn_instance.local.return_value = mock_result
        
        executor = LocalExecutor()
        task = {
            'command': 'echo "hello"',
            'env': {'KEY': 'value'},
            'cwd': '/tmp'
        }
        
        return_code, stdout, stderr = executor.execute_task(task)
        
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
        
        assert return_code == 0
        assert stdout == "test output"
        assert stderr == "test error"
    
    @patch('runner.src.local_executor.BaseExecutor.safe_env')
    def test_execute_task_calls_safe_env(self, mock_safe_env, mock_connection_setup):
        """Test that execute_task calls safe_env to validate environment"""
        mock_connection, mock_conn_instance = mock_connection_setup
        mock_result = Mock()
        mock_conn_instance.local.return_value = mock_result
        mock_safe_env.return_value = {'SAFE_KEY': 'safe_value'}
        
        executor = LocalExecutor()
        task = {
            'command': 'test',
            'env': {'KEY': 123},  # Non-string value
            'cwd': '/tmp'
        }
        
        executor.execute_task(task)
        
        # Verify safe_env was called
        mock_safe_env.assert_called_once_with({'KEY': 123})
        
        # Verify the safe env was passed to fabric
        mock_conn_instance.local.assert_called_once_with(
            'test',
            env={'SAFE_KEY': 'safe_value'},
            hide=True,
            warn=True
        )
    
    def test_execute_task_default_cwd(self, mock_connection_setup):
        """Test that execute_task uses '.' as default cwd"""
        mock_connection, mock_conn_instance = mock_connection_setup
        mock_result = Mock()
        mock_conn_instance.local.return_value = mock_result
        
        executor = LocalExecutor()
        task = {
            'command': 'test',
            'env': {}
        }
        
        executor.execute_task(task)
        
        mock_conn_instance.cd.assert_called_once_with('.')
    
    def test_execute_task_none_result(self, mock_connection_setup):
        """Test handling when fabric local returns None"""
        mock_connection, mock_conn_instance = mock_connection_setup
        mock_conn_instance.local.return_value = None
        
        executor = LocalExecutor()
        task = {
            'command': 'test',
            'env': {},
            'cwd': '/tmp'
        }
        
        return_code, stdout, stderr = executor.execute_task(task)
        
        assert return_code == 1
        assert stdout == ""
        assert "Command execution failed: result is None" in stderr