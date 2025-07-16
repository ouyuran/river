from invoke.runners import Result
from sdk.src.sandbox.base_sandbox import BaseSandbox, BaseSandboxManager


class ConcreteSandbox(BaseSandbox):
    """Concrete implementation for testing BaseSandbox"""
    def __init__(self, id: str = "test_sandbox_id"):
        super().__init__(id)
    
    def execute(self, command: str, cwd: str, env=None) -> Result:
        return Result(stdout="test_output", stderr="", command=command, shell="", env={}, exited=0)


class TestBaseSandbox:

    def test_init_sets_id(self):
        # Test that __init__ properly sets the id
        sandbox = ConcreteSandbox("test_id")
        assert sandbox.id == "test_id"

    def test_execute_is_abstract(self):
        # Test that execute method is properly implemented in concrete class
        sandbox = ConcreteSandbox()
        result = sandbox.execute("ls", "/tmp", {"VAR": "value"})
        
        assert result.stdout == "test_output"
        assert result.command == "ls"


class TestBaseSandboxManager:

    def test_has_abstract_methods(self):
        # Test that BaseSandboxManager has required abstract methods
        assert hasattr(BaseSandboxManager, 'create')
        assert hasattr(BaseSandboxManager, 'fork')
        assert hasattr(BaseSandboxManager, 'destory')
        assert hasattr(BaseSandboxManager, 'take_snapshot')