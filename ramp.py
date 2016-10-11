import ipdb

from rStream.libs import reddit
from rStream.tests import test_libs_reddit


DEBUG = False
TEST_N = 10


def peek():
    return [x.next_submission for x in stream.subs]


def get_next():
    print("\n\nNexts available: " + str(peek()))
    print("Max from above: " + str(next(stream)))


sub_selection = ['cute', 'aww']
if DEBUG:
    setattr(reddit.REDDIT, 'get_subreddit', lambda x: x)
    sub_selection = test_libs_reddit.mock_subs

subs = reddit.SubredditsStream(subreddits=sub_selection,
                               key=lambda x: x.score,
                               func='get_hot')
stream = reddit.submission_filter(subs)

for __ in range(TEST_N):
    print(next(stream))
else:
    ipdb.set_trace()
