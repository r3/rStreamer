import configparser
import os
from urllib import parse

from rStream import CONFIG_FILE


def ext_from_url(url):
    path = parse.urlparse(url).path
    cleaned_path = path[1:]
    __, extension = os.path.splitext(cleaned_path)
    return extension


class DirectLinkManager():
    _config = None
    accepted_extensions = []

    def __init__(self):
        if self._config is None:
            self.configure()

    @classmethod
    def configure(cls):
        cls._config = configparser.ConfigParser()

        with open(CONFIG_FILE) as source:
            cls._config.read_file(source)
        extensions = cls._config.get('directlink', 'AcceptedExtensions')
        cls.accepted_extensions = extensions.split(',')

    @classmethod
    def match(cls, url):
        return ext_from_url(url) in cls.accepted_extensions
