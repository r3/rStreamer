import time
import threading

import pytest

from rStream.libs import cache


class TestExpirationTimer():
    def test_passing_of_args_and_execution(self):
        def testfunc(*args, **kwargs):
            assert 'foo' in args
            assert kwargs['bar'] == 'qux'

        cache.ExpirationTimer(
            0.1,
            testfunc,
            ['foo'],
            {'bar': 'qux'}
        )

    def test_reset(self):
        '''Starts an ExpirationTimer with a timer to call the reset, and
        another to check and ensure that the timer is still running after the
        initial timeout to ensure that the reset took effect
        '''
        def check_test_timer(timer):
            assert timer.is_alive()

        test_timer = cache.ExpirationTimer(0.2, lambda x: x, [None])

        reset_test_timer = threading.Timer(0.1, test_timer.reset)
        reset_test_timer.start()

        polling_timer = threading.Timer(0.3, check_test_timer, [test_timer])
        polling_timer.start()
        polling_timer.join()

    def test_cancellation(self):
        def shouldnt_execute():
            raise Exception("This executes if cancel method fails")

        timer = cache.ExpirationTimer(2.0, shouldnt_execute)
        timer.cancel()
        time.sleep(0.5)  # Takes a moment for cancel to stop the thread
        assert timer.is_alive() is False


def test_Expirable():
    expirable = cache.Expirable('foo', 'bar')
    assert hasattr(expirable, 'stream')
    assert getattr(expirable, 'stream') == 'foo'
    assert hasattr(expirable, 'timeout')
    assert getattr(expirable, 'timeout') == 'bar'


class TestExpiringDict():
    @pytest.fixture()
    def expiringdict(self):
        return cache.ExpiringDict()

    @pytest.fixture()
    def seeded_dict(self, monkeypatch, expiringdict):
        monkeypatch.setattr(cache, 'TIMEOUT', 0.5)
        expiringdict['foo'] = 'bar'
        return expiringdict

    def test_assignment(self, expiringdict):
        expiringdict['foo'] = 'bar'
        assert 'foo' in expiringdict

    def test_lookup(self, seeded_dict):
        assert seeded_dict['foo'] == 'bar'

    def test_deletion(self, seeded_dict):
        del seeded_dict['foo']
        assert 'foo' not in seeded_dict

    def test_get_existing(self, seeded_dict):
        assert seeded_dict.get('foo') == 'bar'

    def test_get_not_existing(self, seeded_dict):
        sentinel = object()
        assert seeded_dict.get('DOESNTEXIST', sentinel) is sentinel
        assert seeded_dict.get('DOESNTEXIST') is None

    def test_timeout(self, seeded_dict):
        assert 'foo' in seeded_dict
        time.sleep(1.0)
        assert 'foo' not in seeded_dict
