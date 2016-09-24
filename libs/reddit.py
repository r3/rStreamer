import praw


user_agent = 'test'  # TODO: Centralize this, and import it properly
REDDIT = praw.Reddit(user_agent=user_agent)


class LazilyEvaluatedWrapper():
    def __init__(self, wrapped):
        self.__wrapped = wrapped


def get_sub_by_name(name):
    return REDDIT.get_subreddit(name)
