import pytest
from sdk.src.job import Job
from unittest.mock import Mock


def test_job_init():
    a = Job('a', lambda: 'A')
    assert a.name == 'a'
    assert a.status == Job.Status.PENDING
    assert a.result is None


def test_job_run():
    a = Job('a', lambda: 'A')
    status, result = a.run()
    assert a.name == 'a'
    assert a.status == Job.Status.SUCCESS
    assert a.result == 'A'
    assert result == 'A'
    assert status == Job.Status.SUCCESS


def test_job_run_failed():
    def main(self):
        raise Exception("Failed")
    a = Job('a', main)

    status, result = a.run()

    assert a.status == Job.Status.FAILED
    assert a.result is None
    assert result is None
    assert status == Job.Status.FAILED

def test_job_run_already_running():
    a = Job('a', lambda: 'A')
    a.run()
    # run again should not raise, should return (status, result)
    status, result = a.run()
    assert result == 'A'
    assert status == Job.Status.SUCCESS
    assert a.status == Job.Status.SUCCESS


def test_job_chain_runs():
    b_holder = {}
    def a_main():
        assert b_holder['b'].status == Job.Status.PENDING
        return 'A'
    a = Job('a', a_main)
    b = Job('b', lambda a: a, upstreams=[a])
    b_holder['b'] = b

    b.run()

    assert a.status == Job.Status.SUCCESS
    assert b.status == Job.Status.SUCCESS


def test_job_upstream_fail_downstream_skip():
    def a_main():
        raise RuntimeError("fail a")
    a = Job('a', a_main)
    b = Job('b', lambda a: a, upstreams=[a])

    status, result = b.run()

    assert a.status == Job.Status.FAILED
    assert b.status == Job.Status.SKIPPED
    assert result is None
    assert status == Job.Status.SKIPPED

def test_job_upstream_name_duplicate_sibling():
    a1 = Job('dup', lambda: 1)
    a2 = Job('dup', lambda: 2)
    main = Job('main', lambda dup: dup, upstreams=[a1, a2])

    with pytest.raises(ValueError, match="Duplicate upstream job name detected: 'dup'"):
        main.run()


def test_job_upstream_name_duplicate_parent():
    a1 = Job('dup', lambda: 1)
    a2 = Job('dup', lambda: 2, upstreams=[a1])
    main = Job('main', lambda dup: dup, upstreams=[a2])

    with pytest.raises(ValueError, match="Duplicate upstream job name detected: 'dup'"):
        main.run()


def test_job_main_param_not_match_upstream():
    a = Job('a', lambda: 1)
    b = Job('b', lambda: 2)
    c = Job('c', lambda missing: missing, upstreams=[a, b])
    with pytest.raises(ValueError, match="do not match any upstream job name"):
        c.run()


def test_job_cycle_detection_raises():
    a = Job('a', lambda: 1)
    b = Job('b', lambda a: a, upstreams=[a])

    with pytest.raises(ValueError, match="would create a cycle"):
        a._join([b])


def test_job_diamond_dependency():
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
    b = Job('b', lambda: 2, upstreams=[a])
    c = Job('c', lambda: 3, upstreams=[a])
    d = Job('d', lambda: 4, upstreams=[b, c])

    d.run()

    assert fn_call_count == 1
    assert a.status == Job.Status.SUCCESS
    assert b.status == Job.Status.SUCCESS
    assert d.status == Job.Status.SUCCESS
    assert c.status == Job.Status.SUCCESS
