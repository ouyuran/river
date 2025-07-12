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
        print(stderr)
        return proc.returncode, stdout.decode(), stderr.decode()
