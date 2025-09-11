from typing import Callable
from invoke.runners import Result
from sdk.river_sdk.sandbox.base_sandbox import BaseSandbox, BaseSandboxManager
from unittest.mock import Mock


class ConcreteSandbox(BaseSandbox):
    """Concrete implementation for testing BaseSandbox"""
    def __init__(self, id: str = "test_sandbox_id"):
        super().__init__(id)
    
    def execute(self, command: str, cwd: str, env=None) -> Result:
        return Result(stdout="test_output", stderr="", command=command, shell="", env={}, exited=0)


class ConcreteSandboxManager(BaseSandboxManager):
    """Concrete implementation for testing BaseSandboxManager"""
    def creator(self) -> Callable[[], BaseSandbox]:
        return self.create
    
    def create(self) -> BaseSandbox:
        return ConcreteSandbox("created_sandbox")
    
    def fork(self, sandbox: BaseSandbox) -> BaseSandbox:
        return ConcreteSandbox(f"forked_{sandbox.id}")
    
    def destory(self, sandbox: BaseSandbox) -> None:
        pass
    
    def take_snapshot(self, sandbox: BaseSandbox) -> str:
        return f"snapshot_{sandbox.id}"


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
    
    def test_forker_returns_callable(self):
        # Test that forker returns a callable
        manager = ConcreteSandboxManager()
        sandbox = ConcreteSandbox("test_sandbox")
        
        forker_fn = manager.forker(sandbox)
        
        assert callable(forker_fn)
    
    def test_forker_callable_forks_sandbox(self):
        # Test that the callable returned by forker actually forks the sandbox
        manager = ConcreteSandboxManager()
        original_sandbox = ConcreteSandbox("original_sandbox")
        
        forker_fn = manager.forker(original_sandbox)
        forked_sandbox = forker_fn()
        
        assert forked_sandbox.id == "forked_original_sandbox"
        assert forked_sandbox.id != original_sandbox.id
    
    def test_forker_callable_no_arguments(self):
        # Test that the callable returned by forker takes no arguments
        manager = ConcreteSandboxManager()
        sandbox = ConcreteSandbox("test_sandbox")
        
        forker_fn = manager.forker(sandbox)
        
        # Should be able to call with no arguments
        result = forker_fn()
        assert isinstance(result, BaseSandbox)
    
    def test_forker_preserves_sandbox_type(self):
        # Test that forker preserves the type of the sandbox
        manager = ConcreteSandboxManager()
        sandbox = ConcreteSandbox("typed_sandbox")
        
        forker_fn = manager.forker(sandbox)
        forked_sandbox = forker_fn()
        
        assert type(forked_sandbox) == type(sandbox)
        assert isinstance(forked_sandbox, ConcreteSandbox)