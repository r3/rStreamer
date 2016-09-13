import configparser
import os
from urllib import parse

from rStream import CONFIG_FILE


# TODO: http://imgur.com/ajaxalbums/getimages/ALBUM_ID/hit.json


def ext_from_url(url):
    path = parse.urlparse(url).path
    if path.startswith('/'):
        path = path[1:]
    if not path:
        return ''
    __, extension = os.path.splitext(path)
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

    @classmethod
    def get_images(cls, url):
        yield url


class GfycatManager():
    @classmethod
    def match(cls, url):
        parsed = parse.urlparse(url)
        return 'gfycat.com' in parsed.netloc and parsed.path != '/'

    @classmethod
    def get_images(cls, url):
        file_name = parse.urlparse(url).path
        name, extension = os.path.splitext(file_name)
        if not extension:
            extension = '.gif'
        if name.startswith('/'):
            name = name[1:]
        if name:
            yield 'http://giant.gfycat.com/{}{}'.format(name, extension)


class ImgurManager():
    _config = None

    def __init__(self):
        if self._config is None:
            self.configure()

    @classmethod
    def configure(cls):
        cls._config = dict()
