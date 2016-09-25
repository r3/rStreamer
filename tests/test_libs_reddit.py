from praw import errors
import pytest

from rStream.libs import reddit


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


class TestSubredditsStream():
    def test_has_subs_after_initialization(self):
        selected = ['foo', 'bar', 'baz']
        stream = reddit.SubredditsStream(selected,
                                         sort_func=lambda x, y: x > y)
        assert stream.subs == selected
