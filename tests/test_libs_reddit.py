from collections import namedtuple

from praw import errors
import pytest

from rStream.libs import reddit


#################### MOCKS ###############################################


class MockSubreddit():
    """Mock of praw.object.Subreddit and supports query methods like get_hot

    Any attempt to use a query method that begins with 'get_' will return an
    iterable from the container of submissions passed at instantiation. No
    other attributes or methods supported
    """
    def __init__(self, name, submissions=None):
        self.dispay_name = self.name = name
        self.submissions = submissions if submissions is not None else []

    def __getattr__(self, attr):
        def func(*args, **kwargs):
            return iter(self.submissions)

        if 'get_' in attr:
            return func


class MockSourceManager():
    """Should mock the libs.SubredditsStream for use in testing

    Limited results have been hard coded to MockSourceManager.results
    and all queries are simply getting values from the results table
    """
    results = {
        'http://test.com/1': ['a'],
        'http://test.com/2': ['a', 'b'],
        'http://test.com/3': ['a', 'b', 'c']
    }

    def __init__(*args, **kwargs):
        pass

    @classmethod
    def match(cls, url):
        return url in cls.results

    @classmethod
    def get_images(cls, url):
        return cls.results.get(url)


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

#################### TESTS ###############################################


def test_info_from_submission():
    MockSubmission = namedtuple('MockSubmission', ['url',
                                                   'score',
                                                   'title',
                                                   'over_18',
                                                   'permalink',
                                                   'subreddit',
                                                   'created'])
    test_submission = MockSubmission(
        url='http://test.com/1',
        score=23,
        title='Test Submission in Test Subreddit',
        over_18=False,
        permalink='http://test.com/test',
        subreddit=MockSubreddit('Test Subreddit'),
        created=12345.0
    )
    extracted = reddit.info_from_submission(test_submission,
                                            MockSourceManager())

    assert extracted['url'] == test_submission.url
    assert extracted['score'] == test_submission.score
    assert extracted['title'] == test_submission.title
    assert extracted['nsfw'] == test_submission.over_18
    assert extracted['link'] == test_submission.permalink
    assert extracted['date'] == test_submission.created
    assert extracted['images'] == ['a']


def test_submission_filter(monkeypatch):
    """Class of tests should ensure correctness of libs.submission_filter
    """
    # Used to simulate a result with an attribute named 'url'
    HasUrl = namedtuple('HasUrl', ['url'])

    def mock_iterable():
        """Stand in for a praw.objects.Subreddit with contents

        Should pass items that will be accepted by the filter, and some that
        are filtered out.
        """
        yield from iter([
            HasUrl('http://test.com/1'),
            HasUrl('http://foo.bar/'),  # Shouldn't get past filter
            HasUrl('http://test.com/2'),
            HasUrl('http://bar.baz/'),  # Shouldn't get past filter
            HasUrl('http://test.com/3')
        ])

    # Inject mocks and bypass info_from_submission function by using
    # get_images on the MockSourceManager directly
    monkeypatch.setattr(reddit.source_managers,
                        'SOURCE_MANAGERS',
                        [MockSourceManager])
    monkeypatch.setattr(reddit,
                        'info_from_submission',
                        lambda x, y: MockSourceManager.get_images(x.url))

    # Get a filtered content stream
    filtered = reddit.submission_filter(mock_iterable())

    # And ensure that unsupported links are filtered and supported links are
    # returned via iteration methods
    assert next(filtered) == ['a']
    assert next(filtered) == ['a', 'b']
    assert next(filtered) == ['a', 'b', 'c']

    # Should raise a StopIteration after generator is expended
    with pytest.raises(StopIteration):
        next(filtered)


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
