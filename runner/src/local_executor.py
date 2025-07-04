import subprocess

from runner.src.base_executor import BaseExecutor

class LocalExecutor(BaseExecutor):
    def execute_task(self, task):
        proc = subprocess.Popen(
            [task['executable'], '-c', task['script']],
            cwd=task['cwd'],
            env=task['env'],
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = proc.communicate()
        return proc.returncode, stdout.decode('utf-8'), stderr.decode('utf-8')
