import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from runner.src.debug_executor import DebugExecutor

class TestDebugExecutor:
    
    def test_execute_task_basic(self):
        """Test basic task execution returns expected debug output"""
        executor = DebugExecutor()
        task = {
            'command': 'echo "hello"',
            'env': {'TEST': 'value'},
            'cwd': '/tmp'
        }
        
        return_code, stdout, stderr = executor.execute_task(task)
        
        assert return_code == 0
        assert stdout == "[DebugExecutor] Simulated stdout"
        assert stderr == "[DebugExecutor] Simulated stderr"
