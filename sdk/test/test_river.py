import pytest
from unittest.mock import Mock
from sdk.river_sdk.river import River, get_current_river, RiverContext, RiverContextError
from sdk.river_sdk.sandbox.base_sandbox import BaseSandboxManager
from sdk.river_sdk.job import Job


# Mock Job classes for testing
class MockJob(Job):
    def __init__(self, name: str, upstreams=None, sandbox_creator=None):
        super().__init__(name, sandbox_creator, upstreams)
        self.main_called = False
        self.return_value = f"result_{name}"
    
    def main(self):
        self.main_called = True
        return self.return_value


class TestRiver:
    def test_init_stores_all_parameters(self):
        mock_manager = Mock(spec=BaseSandboxManager)
        mock_job = MockJob("test_job")
        outlets = {"default": mock_job}
        
        river = River(
            name="test-river",
            sandbox_manager=mock_manager,
            outlets=outlets,
            default_sandbox_config={"image": "ubuntu"},
            max_parallel_jobs=3
        )
        
        assert river.name == "test-river"
        assert river.sandbox_manager is mock_manager
        assert river.outlets == outlets
        assert river.default_sandbox_config == {"image": "ubuntu"}
        assert river.max_parallel_jobs == 3

    def test_init_with_minimal_parameters(self):
        mock_manager = Mock(spec=BaseSandboxManager)
        mock_job = MockJob("test_job")
        outlets = {"default": mock_job}
        
        river = River(
            name="minimal-river",
            sandbox_manager=mock_manager,
            outlets=outlets
        )
        
        assert river.name == "minimal-river"
        assert river.default_sandbox_config is None
        assert river.max_parallel_jobs == 1


    def test_run_default_outlet(self):
        mock_manager = Mock(spec=BaseSandboxManager)
        mock_job = MockJob("test_job")
        
        river = River(
            name="test-river",
            sandbox_manager=mock_manager,
            outlets={"default": mock_job}
        )
        
        river.flow()
        
        assert mock_job.main_called

    def test_run_specific_outlet(self):
        mock_manager = Mock(spec=BaseSandboxManager)
        job1 = MockJob("job1")
        job2 = MockJob("job2", upstreams=[job1])
        
        river = River(
            name="test-river",
            sandbox_manager=mock_manager,
            outlets={
                "default": job2,
                "partial": job1
            }
        )
        
        # Run partial outlet
        river.flow("partial")
        
        assert job1.main_called
        assert not job2.main_called

    def test_run_nonexistent_outlet_raises_error(self):
        mock_manager = Mock(spec=BaseSandboxManager)
        mock_job = MockJob("test_job")
        
        river = River(
            name="test-river",
            sandbox_manager=mock_manager,
            outlets={"default": mock_job}
        )
        
        with pytest.raises(ValueError, match="Outlet 'nonexistent' not found"):
            river.flow("nonexistent")


class TestRiverContext:
    """Test cases for RiverContext class."""

    def test_river_context_sets_and_resets_context(self):
        """Test RiverContext as context manager sets and resets context properly."""
        mock_manager = Mock(spec=BaseSandboxManager)
        mock_job = MockJob("test_job")
        
        river = River(
            name="test-river",
            sandbox_manager=mock_manager,
            outlets={"default": mock_job}
        )
        
        # Initially no river in context
        with pytest.raises(RiverContextError):
            get_current_river()
        
        with RiverContext(river):
            # Inside context manager, river should be available
            current = get_current_river()
            assert current is river
            assert current.sandbox_manager is mock_manager
        
        # After exiting context, river should be cleared
        with pytest.raises(RiverContextError):
            get_current_river()

    def test_river_context_init(self):
        """Test RiverContext initialization."""
        mock_manager = Mock(spec=BaseSandboxManager)
        mock_job = MockJob("test_job")
        river = River("test-river", mock_manager, {"default": mock_job})
        
        context = RiverContext(river)
        assert context._river is river

    def test_river_context_get_current_static_method(self):
        """Test RiverContext.get_current() static method."""
        mock_manager = Mock(spec=BaseSandboxManager)
        mock_job = MockJob("test_job")
        river = River("test-river", mock_manager, {"default": mock_job})
        
        with RiverContext(river):
            # Should return the same river as get_current_river()
            current_from_context = RiverContext.get_current()
            current_from_function = get_current_river()
            assert current_from_context is current_from_function
            assert current_from_context is river

    def test_river_context_exception_cleanup(self):
        """Test that RiverContext cleans up even if exception occurs inside."""
        mock_manager = Mock(spec=BaseSandboxManager)
        mock_job = MockJob("test_job")
        river = River("test-river", mock_manager, {"default": mock_job})
        
        # Verify context is cleaned up even if exception occurs inside
        with pytest.raises(ValueError):
            with RiverContext(river):
                assert get_current_river() is river
                raise ValueError("Test exception")
        
        # Context should still be cleared after exception
        with pytest.raises(RiverContextError):
            get_current_river()

    def test_get_current_river_outside_context_raises_error(self):
        """Test that get_current_river() raises RiverContextError when called outside context."""
        with pytest.raises(RiverContextError, match="get_current_river\\(\\) can only be called within a river context"):
            get_current_river()

