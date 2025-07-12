class BaseExecutor:
    def execute_task(self, task):
        raise NotImplementedError("Subclasses must implement this method")

    @staticmethod
    def safe_env(env):
        """Convert environment variables to str-str dictionary"""
        if not env:
            return {}
        
        safe_env_dict = {}
        for key, value in env.items():
            # Validate and convert key
            if key is None:
                raise ValueError("Environment variable key cannot be None")
            
            try:
                key_str = str(key)
            except:
                raise ValueError(f"Environment variable key cannot be converted to string: {key}")
            
            if not key_str:
                raise ValueError("Environment variable key cannot be empty string")
            
            # Validate and convert value
            try:
                value_str = str(value) if value is not None else ""
            except:
                raise ValueError(f"Environment variable value cannot be converted to string: {value}")
            
            safe_env_dict[key_str] = value_str
        
        return safe_env_dict
        