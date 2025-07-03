import json
from typing import Dict, Optional

class ShellTask:
    def __init__(self, script: str, workdir: Optional[str] = None, shell: str = "/bin/bash", env: Optional[Dict[str, str]] = None):
        self.script = script
        self.workdir = workdir
        self.shell = shell
        self.env = env or {}

    def execute(self):
        data = {
            "type": "shell",
            "script": self.script,
            "workdir": self.workdir,
            "shell": self.shell,
            "env": self.env
        }
        print(data)
