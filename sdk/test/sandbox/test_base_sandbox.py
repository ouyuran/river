from unittest.mock import Mock, patch
from invoke.runners import Result
from sdk.src.sandbox.base_sandbox import BaseSandbox, SandboxProxy


class ConcreteSandbox(BaseSandbox):
    """Concrete implementation for testing BaseSandbox"""
    def _create_impl(self) -> str:
        return "test_sandbox_id"
    
    def _destory_impl(self, sandbox_id: str) -> None:
        pass
    
    def _take_snapshot_impl(self, sandbox_id: str) -> str:
        return "test_snapshot_id"
    
    def execute(self, command: str, cwd: str, env=None) -> Result:
        return Result(stdout="test_output", stderr="", command=command, shell="", env={}, exited=0)


class TestBaseSandbox:

    def test_create_sets_id_and_returns_it(self):
        # Test that create() calls _create_impl and sets self.id
        sandbox = ConcreteSandbox()
        result = sandbox.create()
        
        assert result == "test_sandbox_id"
        assert sandbox.id == "test_sandbox_id"

    def test_destory_calls_impl_and_clears_id(self):
        # Test that destory() calls _destory_impl with correct id and clears self.id
        sandbox = ConcreteSandbox()
        sandbox.id = "test_id"
        
        with patch.object(sandbox, '_destory_impl') as mock_destory:
            sandbox.destory()
            
            mock_destory.assert_called_once_with("test_id")
            assert sandbox.id == ""

    def test_take_snapshot_calls_impl_with_id(self):
        # Test that take_snapshot() calls _take_snapshot_impl with correct id
        sandbox = ConcreteSandbox()
        sandbox.id = "test_id"
        
        with patch.object(sandbox, '_take_snapshot_impl', return_value="snapshot_456") as mock_snapshot:
            result = sandbox.take_snapshot()
            
            mock_snapshot.assert_called_once_with("test_id")
            assert result == "snapshot_456"


class TestSandboxProxy:
    def setup_method(self):
        self.mock_sandbox = Mock(spec=BaseSandbox)
        self.proxy = SandboxProxy(self.mock_sandbox)

    def test_init_stores_sandbox_reference(self):
        assert self.proxy._sandbox is self.mock_sandbox

    def test_execute_delegates_to_sandbox(self):
        # Setup mock return value
        expected_result = Result(stdout="output", stderr="", command="ls", shell="", env={}, exited=0)
        self.mock_sandbox.execute.return_value = expected_result
        
        # Call execute through proxy
        result = self.proxy.execute("ls", "/tmp", {"VAR": "value"})
        
        # Verify delegation
        self.mock_sandbox.execute.assert_called_once_with("ls", "/tmp", {"VAR": "value"})
        assert result is expected_result

    def test_proxy_hides_other_methods(self):
        # Verify that proxy doesn't expose other sandbox methods
        assert not hasattr(self.proxy, 'create')
        assert not hasattr(self.proxy, 'destory')
        assert not hasattr(self.proxy, 'take_snapshot')
        assert hasattr(self.proxy, 'execute')