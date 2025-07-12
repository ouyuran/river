from fabric import Connection
from runner.src.base_executor import BaseExecutor

class LocalExecutor(BaseExecutor):
    def __init__(self):
        pass
    
    def execute_task(self, task):
        command = task['command']
        
        try:
            with Connection('localhost') as connection, \
                 connection.cd(task.get('cwd', '.')):
                result = connection.local(
                    command,
                    env=BaseExecutor.safe_env(task.get('env', {})),
                    hide=True,
                    warn=True
                )
            if result:
                return result.return_code, result.stdout, result.stderr
            else:
                return 1, "", "Command execution failed: result is None"
        except Exception as e:
            raise e
