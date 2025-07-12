import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from runner.src.base_executor import BaseExecutor

class TestBaseExecutor:
    
    def test_execute_task_not_implemented(self):
        """Test that BaseExecutor.execute_task raises NotImplementedError"""
        executor = BaseExecutor()
        with pytest.raises(NotImplementedError):
            executor.execute_task({})
    
    def test_safe_env_empty_dict(self):
        """Test safe_env with empty dict"""
        result = BaseExecutor.safe_env({})
        assert result == {}
    
    def test_safe_env_none_input(self):
        """Test safe_env with None input"""
        result = BaseExecutor.safe_env(None)
        assert result == {}
    
    def test_safe_env_valid_strings(self):
        """Test safe_env with valid string key-value pairs"""
        env = {'KEY1': 'value1', 'KEY2': 'value2'}
        result = BaseExecutor.safe_env(env)
        assert result == {'KEY1': 'value1', 'KEY2': 'value2'}
    
    def test_safe_env_int_values(self):
        """Test safe_env converts integer values to strings"""
        env = {'PORT': 8080, 'COUNT': 42}
        result = BaseExecutor.safe_env(env)
        assert result == {'PORT': '8080', 'COUNT': '42'}
    
    def test_safe_env_none_value(self):
        """Test safe_env converts None values to empty strings"""
        env = {'KEY1': None, 'KEY2': 'value'}
        result = BaseExecutor.safe_env(env)
        assert result == {'KEY1': '', 'KEY2': 'value'}
    
    def test_safe_env_none_key_raises_error(self):
        """Test safe_env raises ValueError for None key"""
        env = {None: 'value'}
        with pytest.raises(ValueError, match="Environment variable key cannot be None"):
            BaseExecutor.safe_env(env)
    
    def test_safe_env_empty_string_key_raises_error(self):
        """Test safe_env raises ValueError for empty string key"""
        env = {'': 'value'}
        with pytest.raises(ValueError, match="Environment variable key cannot be empty string"):
            BaseExecutor.safe_env(env)
    
    def test_safe_env_int_key(self):
        """Test safe_env converts integer keys to strings"""
        env = {123: 'value'}
        result = BaseExecutor.safe_env(env)
        assert result == {'123': 'value'}