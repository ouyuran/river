import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from runner.src.local_executor import LocalExecutor

def test_local_executor():
    executor = LocalExecutor()
    
    # Test with a simple echo command
    task = {
        'command': 'python3 -c "print(\'Hello from LocalExecutor\')"',
        'env': {},
        'cwd': '/tmp'
    }
    
    return_code, stdout, stderr = executor.execute_task(task)
    print(f"Local Executor Test:")
    print(f"Return code: {return_code}")
    print(f"Stdout: {stdout}")
    print(f"Stderr: {stderr}")
    print("-" * 50)
    
    # Test with environment variables
    task_with_env = {
        'command': 'echo $TEST_VAR',
        'env': {'TEST_VAR': 'test_value'},
        'cwd': '/tmp'
    }
    
    return_code, stdout, stderr = executor.execute_task(task_with_env)
    print(f"Local Executor Test with Environment:")
    print(f"Return code: {return_code}")
    print(f"Stdout: {stdout}")
    print(f"Stderr: {stderr}")
    print("-" * 50)

if __name__ == "__main__":
    test_local_executor()