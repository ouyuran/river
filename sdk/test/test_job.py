import pytest
from river_sdk.job import Job, JobContext, get_current_job, JobContextError
from river_sdk.river import River, RiverContext
from river_sdk.sandbox.base_sandbox import BaseSandbox, BaseSandboxManager
from unittest.mock import Mock, patch
from river_common.shared import Status


# Concrete Job implementations for testing
class SimpleJob(Job):
    def __init__(self, name: str, return_value: str, sandbox_creator=None, upstreams=None):
        super().__init__(name, sandbox_creator, upstreams)
        self.return_value = return_value
    
    def main(self):
        return self.return_value


class FailingJob(Job):
    def __init__(self, name: str, error_message: str, sandbox_creator=None, upstreams=None):
        super().__init__(name, sandbox_creator, upstreams)
        self.error_message = error_message
    
    def main(self):
        raise Exception(self.error_message)


class CallbackJob(Job):
    def __init__(self, name: str, callback, sandbox_creator=None, upstreams=None):
        super().__init__(name, sandbox_creator, upstreams)
        self.callback = callback
    
    def main(self):
        return self.callback()


class UpstreamAwareJob(Job):
    def __init__(self, name: str, callback, sandbox_creator=None, upstreams=None):
        super().__init__(name, sandbox_creator, upstreams)
        self.callback = callback
    
    def main(self):
        return self.callback(self)


class TestJob:

    @pytest.fixture
    def river_context(self):
        """Fixture that provides a RiverContext with mocked sandbox manager."""
        mock_manager = Mock(spec=BaseSandboxManager)
        mock_manager.snapshot_exists.return_value = False
        # Create a proper JobResult mock instead of None to avoid serialization issues
        from river_sdk.job import JobResult
        mock_job_result = JobResult(Status.SUCCESS, "test_job_id")
        mock_manager.get_job_result_from_snapshot.return_value = mock_job_result
        mock_manager.set_job_result_to_sandbox.return_value = None
        mock_manager.take_snapshot.return_value = "snapshot_id"
        mock_manager.destory.return_value = None
        
        # Create a mock job for the river outlets
        mock_river_job = SimpleJob("river_job", "river_result")
        
        river = River(
            name="test-river",
            sandbox_manager=mock_manager,
            outlets={"default": mock_river_job}
        )
        
        with RiverContext(river):
            yield river

    def test_job_init(self):
        a = SimpleJob('a', 'A')
        assert a.name == 'a'
        assert a.status == Status.PENDING
        assert a.result is None
        assert a.error is None


    def test_job_run(self, river_context):
        a = SimpleJob('a', 'A')
        a.run()

        assert a.name == 'a'
        assert a.status == Status.SUCCESS
        assert a.result.main_return == 'A'


    def test_job_run_failed(self, river_context):
        a = FailingJob('a', "Failed")
        a.run()

        assert a.status == Status.FAILED
        assert a.result.status == Status.FAILED
        assert a.error is not None
        assert str(a.error) == "Failed"

    def test_job_run_already_running(self, river_context):
        a = SimpleJob('a', 'A')
        a.run()
        # run again should not raise since job is already finished
        a.run()
        assert a.result.main_return == 'A'
        assert a.status == Status.SUCCESS


    def test_job_chain_runs(self, river_context):
        b_holder = {}
        def a_main():
            assert b_holder['b'].status == Status.PENDING
            return 'A'
        a = CallbackJob('a', a_main)
        b = SimpleJob('b', 'B', upstreams=[a])
        b_holder['b'] = b

        b.run()

        assert a.status == Status.SUCCESS
        assert b.status == Status.SUCCESS


    def test_job_upstream_fail_downstream_skip(self, river_context):
        a = FailingJob('a', "fail a")
        b = SimpleJob('b', 'B', upstreams=[a])

        b.run()

        assert a.status == Status.FAILED
        assert b.status == Status.SKIPPED


    def test_job_main_param_not_match_upstream(self, river_context):
        # This test needs to be updated since Job.main() doesn't take upstream parameters anymore
        # The upstream values would need to be accessed differently in the new architecture
        a = SimpleJob('a', '1')
        b = SimpleJob('b', '2')
        c = SimpleJob('c', 'C', upstreams=[a, b])
        
        # This test may not be relevant anymore with the new architecture
        # where main() doesn't receive upstream parameters directly
        c.run()
        assert c.status == Status.SUCCESS


    def test_job_cycle_detection_raises(self):
        a = SimpleJob('a', '1')
        b = SimpleJob('b', '2', upstreams=[a])

        with pytest.raises(ValueError, match="would create a cycle"):
            a._join([b])


    def test_job_diamond_dependency(self, river_context):
        """
        a
        / \\
        b  c
        \\ /
        d
        """
        fn_call_count = 0
        def a_main():
            nonlocal fn_call_count
            fn_call_count += 1
            return fn_call_count
        a = CallbackJob('a', a_main)
        b = SimpleJob('b', '2', upstreams=[a])
        c = SimpleJob('c', '3', upstreams=[a])
        d = SimpleJob('d', "4", upstreams=[b, c])

        d.run()

        assert fn_call_count == 1
        assert a.status == Status.SUCCESS
        assert b.status == Status.SUCCESS
        assert d.status == Status.SUCCESS
        assert c.status == Status.SUCCESS


class TestJobSandbox:

    @pytest.fixture
    def river_context(self):
        """Fixture that provides a RiverContext with mocked sandbox manager."""
        mock_manager = Mock(spec=BaseSandboxManager)
        mock_manager.snapshot_exists.return_value = False
        # Create a proper JobResult mock instead of None to avoid serialization issues
        from river_sdk.job import JobResult
        mock_job_result = JobResult(Status.SUCCESS, "test_job_id")
        mock_manager.get_job_result_from_snapshot.return_value = mock_job_result
        mock_manager.set_job_result_to_sandbox.return_value = None
        mock_manager.take_snapshot.return_value = "snapshot_id"
        mock_manager.destory.return_value = None
        
        # Create a mock job for the river outlets
        mock_river_job = SimpleJob("river_job", "river_result")
        
        river = River(
            name="test-river",
            sandbox_manager=mock_manager,
            outlets={"default": mock_river_job}
        )
        
        with RiverContext(river):
            yield river

    @pytest.fixture
    def mock_sandbox(self):
        """Fixture for mock sandbox."""
        sandbox = Mock(spec=BaseSandbox)
        sandbox.id = "test_container_123"
        return sandbox

    @pytest.fixture
    def mock_sandbox_creator(self, mock_sandbox):
        """Fixture for mock sandbox creator."""
        return Mock(return_value=mock_sandbox)

    def test_job_init_with_sandbox_creator(self):
        # Test Job initialization with sandbox_creator
        mock_sandbox_creator = Mock()
        job = SimpleJob('test_job', 'result', sandbox_creator=mock_sandbox_creator)
        
        assert job._sandbox_creator is mock_sandbox_creator
        assert job.sandbox is None

    def test_job_init_without_sandbox_creator(self):
        # Test Job initialization without sandbox_creator
        job = SimpleJob('test_job', 'result')
        
        assert job._sandbox_creator is None
        assert job.sandbox is None

    @patch('cloudpickle.dumps')
    @patch('cloudpickle.loads') 
    def test_job_run_creates_sandbox(self, mock_loads, mock_dumps, river_context, mock_sandbox, mock_sandbox_creator):
        # Test that running a job creates sandbox when sandbox_creator is provided
        # Mock cloudpickle to avoid serialization issues with Mock objects
        mock_dumps.return_value = b'fake_serialized_data'
        mock_loads.return_value = Mock()
        
        job = SimpleJob('test_job', 'result', sandbox_creator=mock_sandbox_creator)
        
        job.run()
        
        mock_sandbox_creator.assert_called_once()
        assert job.sandbox is mock_sandbox
        assert job.status == Status.SUCCESS
        assert job.result.main_return == 'result'
        river_context.sandbox_manager.destory.assert_called_once_with(mock_sandbox)

    def test_job_run_without_sandbox_creator(self, river_context):
        # Test that running a job without sandbox_creator doesn't create sandbox
        job = SimpleJob('test_job', 'result')
        
        job.run()
        
        assert job.sandbox is None
        assert job.status == Status.SUCCESS
        assert job.result.main_return == 'result'
        river_context.sandbox_manager.take_snapshot.assert_not_called()
        river_context.sandbox_manager.destory.assert_not_called()

    @patch('cloudpickle.dumps')
    @patch('cloudpickle.loads')
    def test_job_sandbox_available_in_main(self, mock_loads, mock_dumps, river_context, mock_sandbox, mock_sandbox_creator):
        # Test that sandbox is available in main function through self parameter
        # Mock cloudpickle to avoid serialization issues with Mock objects
        mock_dumps.return_value = b'fake_serialized_data'
        mock_loads.return_value = Mock()
        
        def main_callback(job_self):
            assert job_self.sandbox is mock_sandbox
            return 'success'
        
        job = UpstreamAwareJob('test_job', main_callback, sandbox_creator=mock_sandbox_creator)
        
        job.run()
        
        assert job.status == Status.SUCCESS
        assert job.result.main_return == 'success'
        assert job.sandbox is mock_sandbox
        river_context.sandbox_manager.destory.assert_called_once_with(mock_sandbox)

    def test_job_sandbox_creator_exception_fails_job(self, river_context):
        # Test that exception in sandbox_creator causes job to fail
        mock_sandbox_creator = Mock(side_effect=Exception("Sandbox creation failed"))
        
        job = SimpleJob('test_job', 'result', sandbox_creator=mock_sandbox_creator)
        
        job.run()
        
        assert job.status == Status.FAILED
        assert job.result.status == Status.FAILED
        assert job.sandbox is None
        assert job.error is not None
        assert str(job.error) == "Sandbox creation failed"


class TestJobContext:
    """Test cases for JobContext class."""

    def test_job_context_init(self):
        """Test JobContext initialization with a job."""
        job = SimpleJob('test_job', 'result')
        context = JobContext(job)
        
        assert context._job is job

    def test_job_context_as_context_manager(self):
        """Test JobContext works as context manager."""
        job = SimpleJob('test_job', 'result')
        
        # Initially no job in context
        with pytest.raises(JobContextError):
            get_current_job()
        
        # Inside context manager, job should be available
        with JobContext(job):
            current_job = get_current_job()
            assert current_job is job
        
        # After exiting context, job should be cleared
        with pytest.raises(JobContextError):
            get_current_job()

    def test_job_context_get_current_static_method(self):
        """Test JobContext.get_current() static method."""
        job = SimpleJob('test_job', 'result')
        
        with JobContext(job):
            # Should return the same job as get_current_job()
            current_from_context = JobContext.get_current()
            current_from_function = get_current_job()
            assert current_from_context is current_from_function
            assert current_from_context is job

    def test_job_context_exception_in_context_still_cleans_up(self):
        """Test that JobContext cleans up even if exception occurs inside."""
        job = SimpleJob('test_job', 'result')
        
        # Verify context is cleaned up even if exception occurs inside
        with pytest.raises(ValueError):
            with JobContext(job):
                assert get_current_job() is job
                raise ValueError("Test exception")
        
        # Context should still be cleared after exception
        with pytest.raises(JobContextError):
            get_current_job()

    def test_get_current_job_outside_context_raises_error(self):
        """Test that get_current_job() raises JobContextError when called outside context."""
        with pytest.raises(JobContextError, match="get_current_job\\(\\) can only be called within a job context"):
            get_current_job()
