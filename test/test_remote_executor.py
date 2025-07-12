import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from runner.src.remote_executor import RemoteExecutor

def test_remote_executor():
    # This test assumes you have SSH access to localhost
    # In practice, you would use a real remote host
    try:
        executor = RemoteExecutor('localhost', password='guagua')
        
        task = {
            'command': 'python3 -c "print(\'Hello from RemoteExecutor\')"',
            'env': {},
            'cwd': '/tmp'
        }
        
        return_code, stdout, stderr = executor.execute_task(task)
        print(f"Remote Executor Test:")
        print(f"Return code: {return_code}")
        print(f"Stdout: {stdout}")
        print(f"Stderr: {stderr}")
        print("-" * 50)
        
        # Test with environment variables
        task_with_env = {
            'command': 'echo $REMOTE_VAR',
            'env': {'REMOTE_VAR': 'remote_value'},
            'cwd': '/tmp'
        }
        
        return_code, stdout, stderr = executor.execute_task(task_with_env)
        print(f"Remote Executor Test with Environment:")
        print(f"Return code: {return_code}")
        print(f"Stdout: {stdout}")
        print(f"Stderr: {stderr}")
        print("-" * 50)
    except Exception as e:
        print(f"Remote Executor Test failed: {e}")
        print("-" * 50)

if __name__ == "__main__":
    test_remote_executor()