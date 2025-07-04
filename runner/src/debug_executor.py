from runner.src.base_executor import BaseExecutor

class DebugExecutor(BaseExecutor):
    def execute_task(self, command, **kwargs):
        print(f"[DebugExecutor] Would run: {command} with kwargs: {kwargs}")
        return 0, b"[DebugExecutor] Simulated stdout", b"[DebugExecutor] Simulated stderr"