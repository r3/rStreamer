from praw import errors
import pytest

from rStream.libs import reddit


def test_lazilyevaluatedwrapper():
    class LazyGeneratorWithErrors():
        def iter_raises_clientexception(self):
            yield 0
            raise errors.PRAWException()

    volatile = LazyGeneratorWithErrors().iter_raises_clientexception()
    safe = reddit.LazilyEvaluatedWrapper(volatile, errors.PRAWException)

    assert next(safe) == 0
    with pytest.raises(StopIteration):
        next(safe)


def test_sub_by_name(monkeypatch):
    def mock_getter(*args, **kwargs):
        return 'FooBar'

    monkeypatch.setattr(reddit.REDDIT, 'get_subreddit', mock_getter)
    assert reddit.get_sub_by_name('foo') == 'FooBar'
