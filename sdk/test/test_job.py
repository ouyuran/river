import pytest
from sdk.src.job import Job
from unittest.mock import Mock
from sdk.src.sandbox.base_sandbox import BaseSandbox


class TestJob:

    def test_job_init(self):
        a = Job('a', lambda: 'A')
        assert a.name == 'a'
        assert a.status == Job.Status.PENDING
        assert a.result is None
        assert a.error is None


    def test_job_run(self):
        a = Job('a', lambda: 'A')
        status, result = a.run()
        assert a.name == 'a'
        assert a.status == Job.Status.SUCCESS
        assert a.result == 'A'
        assert result == 'A'
        assert status == Job.Status.SUCCESS


    def test_job_run_failed(self):
        def main(self):
            raise Exception("Failed")
        a = Job('a', main)

        status, result = a.run()

        assert a.status == Job.Status.FAILED
        assert a.result is None
        assert result is None
        assert status == Job.Status.FAILED
        assert a.error is not None
        assert str(a.error) == "Failed"

    def test_job_run_already_running(self):
        a = Job('a', lambda: 'A')
        a.run()
        # run again should not raise, should return (status, result)
        status, result = a.run()
        assert result == 'A'
        assert status == Job.Status.SUCCESS
        assert a.status == Job.Status.SUCCESS


    def test_job_chain_runs(self):
        b_holder = {}
        def a_main():
            assert b_holder['b'].status == Job.Status.PENDING
            return 'A'
        a = Job('a', a_main)
        b = Job('b', lambda a: a, upstreams={'a': a})
        b_holder['b'] = b

        b.run()

        assert a.status == Job.Status.SUCCESS
        assert b.status == Job.Status.SUCCESS


    def test_job_upstream_fail_downstream_skip(self):
        def a_main():
            raise RuntimeError("fail a")
        a = Job('a', a_main)
        b = Job('b', lambda a: a, upstreams={'a': a})

        status, result = b.run()

        assert a.status == Job.Status.FAILED
        assert b.status == Job.Status.SKIPPED
        assert result is None
        assert status == Job.Status.SKIPPED


    def test_job_main_param_not_match_upstream(self):
        a = Job('a', lambda: 1)
        b = Job('b', lambda: 2)
        c = Job('c', lambda missing: missing, upstreams={'a': a, 'b': b})
        with pytest.raises(ValueError, match="do not match any upstream key"):
            c.run()


    def test_job_cycle_detection_raises(self):
        a = Job('a', lambda: 1)
        b = Job('b', lambda a: a, upstreams={'a': a})

        with pytest.raises(ValueError, match="would create a cycle"):
            a._join({'b': b})


    def test_job_diamond_dependency(self):
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
        a = Job('a', a_main)
        b = Job('b', lambda: 2, upstreams={'a': a})
        c = Job('c', lambda: 3, upstreams={'a': a})
        d = Job('d', lambda: 4, upstreams={'b': b, 'c': c})

        d.run()

        assert fn_call_count == 1
        assert a.status == Job.Status.SUCCESS
        assert b.status == Job.Status.SUCCESS
        assert d.status == Job.Status.SUCCESS
        assert c.status == Job.Status.SUCCESS


class TestJobSandbox:

    def test_job_init_with_sandbox_creator(self):
        # Test Job initialization with sandbox_creator
        mock_sandbox_creator = Mock()
        job = Job('test_job', lambda: 'result', sandbox_creator=mock_sandbox_creator)
        
        assert job._sandbox_creator is mock_sandbox_creator
        assert job.sandbox is None

    def test_job_init_without_sandbox_creator(self):
        # Test Job initialization without sandbox_creator
        job = Job('test_job', lambda: 'result')
        
        assert job._sandbox_creator is None
        assert job.sandbox is None

    def test_job_run_creates_sandbox(self):
        # Test that running a job creates sandbox when sandbox_creator is provided
        mock_sandbox = Mock(spec=BaseSandbox)
        mock_sandbox_creator = Mock(return_value=mock_sandbox)
        
        job = Job('test_job', lambda: 'result', sandbox_creator=mock_sandbox_creator)
        
        status, result = job.run()
        
        mock_sandbox_creator.assert_called_once()
        assert job.sandbox is mock_sandbox
        assert status == Job.Status.SUCCESS
        assert result == 'result'

    def test_job_run_without_sandbox_creator(self):
        # Test that running a job without sandbox_creator doesn't create sandbox
        job = Job('test_job', lambda: 'result')
        
        status, result = job.run()
        
        assert job.sandbox is None
        assert status == Job.Status.SUCCESS
        assert result == 'result'

    def test_job_sandbox_available_in_main(self):
        # Test that sandbox is available in main function through self parameter
        mock_sandbox = Mock(spec=BaseSandbox)
        mock_sandbox_creator = Mock(return_value=mock_sandbox)
        
        def main(self):
            assert self.sandbox is mock_sandbox
            return 'success'
        
        job = Job('test_job', main, sandbox_creator=mock_sandbox_creator)
        
        status, result = job.run()
        
        assert status == Job.Status.SUCCESS
        assert result == 'success'
        assert job.sandbox is mock_sandbox

    def test_job_sandbox_creator_exception_fails_job(self):
        # Test that exception in sandbox_creator causes job to fail
        mock_sandbox_creator = Mock(side_effect=Exception("Sandbox creation failed"))
        
        job = Job('test_job', lambda: 'result', sandbox_creator=mock_sandbox_creator)
        
        status, result = job.run()
        
        assert status == Job.Status.FAILED
        assert result is None
        assert job.sandbox is None
        assert job.error is not None
        assert str(job.error) == "Sandbox creation failed"
