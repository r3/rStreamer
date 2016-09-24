from praw import errors

from rStream.libs import reddit


def test_LazilyEvaluatedWrapper():
    class ToWrap():
        def request(self):
            yield from self._first_works()
            yield from self._raises_ClientException()
            yield from self._raises_APIException()
            yield from self._raises_HTTPException()
            yield from self._last_works()

        def _first_works():
            yield 0

        def _raises_ClientException(self):
            raise errors.ClientException()

        def _raises_APIException(self):
            raise errors.APIException()

        def _raises_HTTPException(self):
            raise errors.HTTPException()

        def _last_works():
            yield 1

    wrapped = reddit.LazilyEvaluatedWrapper(ToWrap())
    result = wrapped.request()
    assert list(result) == [1, 2]


def test_sub_by_name(monkeypatch):
    def mock_getter(*args, **kwargs):
        return 'FooBar'

    monkeypatch.setattr(reddit.REDDIT, 'get_subreddit', mock_getter)
    assert reddit.get_sub_by_name('foo') == 'FooBar'
