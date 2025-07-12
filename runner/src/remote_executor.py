from fabric import Connection
from runner.src.base_executor import BaseExecutor

class RemoteExecutor(BaseExecutor):
    def __init__(self, host, user=None, key_filename=None, password=None, port=22):
        self.host = host
        self.user = user
        self.port = port
        
        self.connect_kwargs = {}
        if key_filename:
            self.connect_kwargs['key_filename'] = key_filename
        if password:
            self.connect_kwargs['password'] = password
    
    def execute_task(self, task):
        command = task['command']
        
        try:
            if self.user:
                connection_params = {
                    'host': self.host,
                    'user': self.user,
                    'port': self.port,
                    'connect_kwargs': self.connect_kwargs
                }
            else:
                connection_params = {
                    'host': self.host,
                    'port': self.port,
                    'connect_kwargs': self.connect_kwargs
                }
            
            with Connection(**connection_params) as connection:
                with connection.cd(task.get('cwd', '~')):
                    result = connection.run(
                        command,
                        env=BaseExecutor.safe_env(task.get('env', {})),
                        hide=True,
                        warn=True
                    )
                return result.return_code, result.stdout, result.stderr
        except Exception as e:
            return 1, "", str(e)