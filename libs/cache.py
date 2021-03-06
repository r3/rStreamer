import threading


TIMEOUT = 60.0  # In seconds


class ExpirationTimer():
    def __init__(self, timeout, func, *args, **kwargs):
        self.timeout = timeout
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.reset()

    def reset(self):
        try:
            self.__timer.cancel()
        except AttributeError:
            pass

        self.__timer = threading.Timer(
            self.timeout,
            self.func,
            *self.args,
            **self.kwargs
        )

        self.__timer.start()

    def start(self):
        self.__timer.start()

    def cancel(self):
        self.__timer.cancel()

    def is_alive(self):
        return self.__timer.is_alive()


class Expirable():
    def __init__(self, stream, timeout=None):
        self.stream = stream
        self.timeout = timeout


class ExpiringDict(dict):
    def __init__(self, *args, **kwargs):
        self.lock = threading.Lock()
        super().__init__(*args, **kwargs)

    def __getitem__(self, key):
        with self.lock:
            value = super().__getitem__(key)

        value.timeout.reset()
        return value.stream

    def __setitem__(self, key, value):
        timer = ExpirationTimer(TIMEOUT, self.__delitem__, [key])
        wrapped = Expirable(value, timer)

        with self.lock:
            super().__setitem__(key, wrapped)

    def __delitem__(self, key):
        with self.lock:
            try:
                value = super().__getitem__(key)
                value.timeout.cancel()
                super().__delitem__(key)
            except KeyError:
                return

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def clear(self, *args, **kwargs):
        raise NotImplementedError()

    def copy(self, *args, **kwargs):
        raise NotImplementedError()

    def fromkeys(self, *args, **kwargs):
        raise NotImplementedError()

    def items(self, *args, **kwargs):
        raise NotImplementedError()

    def keys(self, *args, **kwargs):
        raise NotImplementedError()

    def pop(self, *args, **kwargs):
        raise NotImplementedError()

    def popitem(self, *args, **kwargs):
        raise NotImplementedError()

    def setdefault(self, *args, **kwargs):
        raise NotImplementedError()

    def update(self, *args, **kwargs):
        raise NotImplementedError()

    def values(self, *args, **kwargs):
        raise NotImplementedError()
