import pytest
from sdk.src.job import Job
from unittest.mock import Mock


class TestJob:

    def test_job_init(self):
        a = Job('a', lambda: 'A')
        assert a.name == 'a'
        assert a.status == Job.Status.PENDING
        assert a.result is None


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
