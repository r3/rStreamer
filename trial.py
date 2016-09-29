from rStream.libs import reddit
from rStream.tests import test_libs_reddit


def peek():
    return [x.next_submission for x in stream.subs]


def get_next():
    print("\n\nNexts available: " + str(peek()))
    print("Max from above: " + str(next(stream)))


setattr(reddit.REDDIT, 'get_subreddit', lambda x: x)

stream = reddit.SubredditsStream(subreddits=test_libs_reddit.mock_subs,
                                 key=lambda x: x.score,
                                 func='get_got')

get_next()
get_next()
get_next()
get_next()
get_next()
get_next()
get_next()
get_next()
get_next()
get_next()
get_next()
