from collections import namedtuple

from praw import errors
import pytest

from rStream.libs import reddit


class MockSubreddit():
    def __init__(self, name, submissions):
        self.name = name
        self.submissions = submissions

    def __getattr__(self, attr):
        def func(*args, **kwargs):
            return iter(self.submissions)

        if 'get_' in attr:
            return func

MockSubmission = namedtuple('MockSubmission', ('id', 'score', 'created_utc'))


foo = MockSubreddit('foo', [
    MockSubmission(id='foo3', score=7, created_utc=3000000001.0),
    MockSubmission(id='foo2', score=2, created_utc=2000000001.0),
    MockSubmission(id='foo1', score=1, created_utc=1000000001.0)
])
bar = MockSubreddit('bar', [
    MockSubmission(id='bar3', score=8, created_utc=3000000002.0),
    MockSubmission(id='bar2', score=4, created_utc=2000000002.0),
    MockSubmission(id='bar1', score=3, created_utc=1000000002.0)
])
baz = MockSubreddit('baz', [
    MockSubmission(id='baz3', score=9, created_utc=3000000003.0),
    MockSubmission(id='baz2', score=6, created_utc=2000000003.0),
    MockSubmission(id='baz1', score=5, created_utc=1000000003.0)
])

order_by_score = ['baz3', 'bar3', 'foo3', 'baz2', 'baz1', 'bar2', 'bar1',
                  'foo2', 'foo1']
order_by_created_utc = ['baz3', 'bar3', 'foo3', 'baz2', 'bar2', 'foo2',
                        'baz1', 'bar1', 'foo1']

mock_subs = (foo, bar, baz)


class TestSubredditsStream():
    def _identity(self, name):
        return name

    @pytest.fixture()
    def stream_by_date(self, monkeypatch):
        def by_date(x):
            return x.created_utc
        monkeypatch.setattr(reddit.REDDIT, 'get_subreddit', self._identity)
        return reddit.SubredditsStream(mock_subs, key=by_date, func='get_hot')

    @pytest.fixture()
    def stream_by_score(self, monkeypatch):
        def by_score(x):
            return x.score
        monkeypatch.setattr(reddit.REDDIT, 'get_subreddit', self._identity)
        return reddit.SubredditsStream(mock_subs, key=by_score, func='get_hot')

    def test_has_subs_after_initialization(self, stream_by_date):
        assert stream_by_date.subs

    def test_stream_is_iterable(self, stream_by_date):
        assert hasattr(stream_by_date, '__next__')

    def test_stream_order_by_score(self, stream_by_score):
        results = [x.id for x in stream_by_score]
        assert results == order_by_score

    def test_stream_order_by_date(self, stream_by_date):
        results = [x.id for x in stream_by_date]
        assert results == order_by_created_utc


class TestLazilyEvaluatedWrapper():
    def test_stopiteration_on_exception(self):
        def broken_gen():
            yield 0
            raise errors.PRAWException()

        safe = reddit.LazilyEvaluatedWrapper(broken_gen(), errors.PRAWException)

        assert next(safe) == 0
        with pytest.raises(StopIteration):
            next(safe)

    def test_get_existing_attrib(self):
        class HasFoo():
            def __init__(self):
                self.foo = 'bar'

        # Error should not be raised, so which errors are caught are
        # caught unimportant. but must be valud for `except` statement
        safe = reddit.LazilyEvaluatedWrapper(HasFoo(), errors.PRAWException)
        assert safe.foo == 'bar'

    def test_get_missing_attrib_without_sentinel(self):
        safe = reddit.LazilyEvaluatedWrapper([], errors.PRAWException)
        with pytest.raises(AttributeError):
            assert safe.missing

    def test_get_missing_attrib_watching_AttributeError(self):
        safe = reddit.LazilyEvaluatedWrapper([], AttributeError)
        with pytest.raises(AttributeError):
            assert safe.missing

    def test_get_missing_attrib_with_sentinel(self):
        safe = reddit.LazilyEvaluatedWrapper([],
                                             AttributeError,
                                             sentinel='foo')
        assert safe.missing == 'foo'
