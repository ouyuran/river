class BaseExecutor:
    def execute_task(self, task):
        raise NotImplementedError("Subclasses must implement this method")
