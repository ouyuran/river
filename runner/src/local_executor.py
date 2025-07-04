import subprocess

from runner.src.base_executor import BaseExecutor

class LocalExecutor(BaseExecutor):
    def execute_task(self, command, **kwargs):
        proc = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            **kwargs
        )
        stdout, stderr = proc.communicate()
        return proc.returncode, stdout, stderr
