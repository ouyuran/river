from runner.src.base_executor import BaseExecutor

class DebugExecutor(BaseExecutor):
    def execute_task(self, task):
        print(f"[DebugExecutor] Would run: {task}")
        return 0, "[DebugExecutor] Simulated stdout", "[DebugExecutor] Simulated stderr"
