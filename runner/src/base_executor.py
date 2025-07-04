class BaseExecutor:
    def execute_task(self, command, **kwargs):
        raise NotImplementedError("Subclasses must implement this method")
