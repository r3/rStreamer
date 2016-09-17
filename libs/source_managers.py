import configparser
import json
import os
from urllib import parse, request

from rStream import CONFIG_FILE


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
        if cls.match(url):
            yield url


class GfycatManager():
    @classmethod
    def match(cls, url):
        parsed = parse.urlparse(url)
        if 'giant' in parsed.netloc and ext_from_url(url) == '':
            return False
        return 'gfycat.com' in parsed.netloc and parsed.path != '/'

    @classmethod
    def get_images(cls, url):
        file_name = parse.urlparse(url).path
        name, __ = os.path.splitext(file_name)
        if name.startswith('/'):
            name = name[1:]
        if name:
            yield 'http://giant.gfycat.com/{}.gif'.format(name)


class ImgurManager():
    image_template = 'http://i.imgur.com/{}'
    album_template = 'http://imgur.com/ajaxalbums/getimages/{}/hit.json'

    @classmethod
    def match(cls, url):
        parsed = parse.urlparse(url)
        return 'imgur.com' in parsed.netloc and parsed.path != '/'

    @classmethod
    def get_images(cls, url):
        if not cls.match(url):
            return

        parsed = parse.urlparse(url)

        if parsed.path.startswith('/a/'):
            index = -2 if parsed.path.endswith('/') else -1
            album_id = parsed.path.split('/')[index]
            album_json = cls.album_template.format(album_id)
            with request.urlopen(album_json) as response:
                raw = response.read()
                results = json.loads(raw.decode())

            for result in results['data']['images']:
                image_id = result['hash'] + result['ext']
                yield cls.image_template.format(image_id)
        else:
            if parsed.path.endswith('/'):
                path = parsed.path[:-1]
            else:
                path = parsed.path

            image_id = path.split('/')[-1]
            yield cls.image_template.format(image_id)
