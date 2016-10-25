import logging

import praw

from rStream.libs import source_managers


logger = logging.getLogger('__main__')

user_agent = 'test'  # TODO: Centralize this, and import it properly
REDDIT = praw.Reddit(user_agent=user_agent)


def submission_filter(iterable):
    for submission in iterable:
        for manager in source_managers.SOURCE_MANAGERS:
            if manager.match(submission.url):
                msg = "Found manager to support url, '{}'"
                logger.info(msg.format(submission.url))
                yield [x for x in manager.get_images(submission.url)]


class SubredditsStream():
    class SubredditWrapper():
        def __init__(self, name, func):
            subreddit = REDDIT.get_subreddit(name)

            self.subreddit = subreddit
            query_func = getattr(subreddit, func)
            self.__submission_gen = query_func(limit=None)
            self.next_submission = next(self.__submission_gen)

            msg = "Creating wrapper for subreddit '{}'."
            logger.info(msg.format(self.subreddit.display_name))

        def __next__(self):
            if self.next_submission is None:
                raise StopIteration

            result = self.next_submission
            try:
                self.next_submission = next(self.__submission_gen)
            except StopIteration:
                msg = "Wrapped subreddit '{}' is expended."
                logger.info(msg.format(self.subreddit.display_name))
                self.next_submission = None

            return result

        def __str__(self):
            return self.subreddit.id

    def _getter(self, wrapped_subreddit):
        next_submission = wrapped_subreddit.next_submission
        if next_submission is None:
            return -1

        return self.key(next_submission)

    def __init__(self, subreddits, key, func):
        self.subs = [self.SubredditWrapper(x, func) for x in subreddits]
        self.key = key
        logger.debug("SubredditsStream initialized")

    def __next__(self):
        subreddit = max(self.subs, key=self._getter)
        result = next(subreddit)
        if result is None:
            logger.info("No further content from SubredditsStream")
            raise StopIteration
        return result

    def __iter__(self):
        while True:
            try:
                yield next(self)
            except StopIteration:
                break


class LazilyEvaluatedWrapper():
    def __init__(self, wrapped, to_catch, sentinel=None):
        self.__wrapped = wrapped
        self.to_catch = to_catch
        self.sentinel = sentinel

    def __next__(self):
        try:
            return next(self.__wrapped)
        except self.to_catch:
            raise StopIteration

    def __getattr__(self, attr):
        try:
            return getattr(self.__wrapped, attr)
        except self.to_catch:
            if self.sentinel is not None:
                return self.sentinel
            else:
                raise
