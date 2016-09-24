import praw


user_agent = 'test'  # TODO: Centralize this, and import it properly
REDDIT = praw.Reddit(user_agent=user_agent)


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
            return self.sentinel


def get_sub_by_name(name):
    return REDDIT.get_subreddit(name)
