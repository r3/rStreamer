from pprint import pprint
import logging

import pdb

from rStream.libs import reddit
from rStream.tests import test_libs_reddit


DEBUG = False
TEST_N = 1

logger = logging.getLogger(__name__)


def _peek():
    return {x.next_submission.url: x.next_submission.title for x in subs.subs}


def peek():
    pprint(_peek())


def scores():
    return {x.next_submission.title: x.next_submission.score for x in subs.subs}


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

results = []
while True:
    if len(results) > 100:
        break

    try:
        results.append(next(stream))
    except Exception as err:
        pass

pdb.set_trace()
