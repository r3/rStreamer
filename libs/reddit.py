import praw


user_agent = 'test'  # TODO: Centralize this, and import it properly
REDDIT = praw.Reddit(user_agent=user_agent)


class LazilyEvaluatedWrapper():
    def __init__(self, wrapped, to_catch):
        self.__wrapped = wrapped
        self.to_catch = to_catch

    def catch_exceptions(self, func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except self.to_catch as err:
            raise StopIteration(err)

    def __next__(self):
        return self.catch_exceptions(next, self.__wrapped)

    def __getattr__(self, attr):
        return self.catch_exceptions(getattr, self.__wrapped, attr)


def get_sub_by_name(name):
    return REDDIT.get_subreddit(name)
