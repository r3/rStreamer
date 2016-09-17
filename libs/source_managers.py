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
    def _get_single_image(cls, parsed):
        if parsed.path.endswith('/'):
            path = parsed.path[:-1]
        else:
            path = parsed.path

        image_id = path.split('/')[-1]
        yield cls.image_template.format(image_id)

    @classmethod
    def _get_album(cls, parsed):
        if parsed.path.endswith('/'):
            path = parsed.path[:-1]
        else:
            path = parsed.path

        *__, album_id = path.split('/')
        json_address = cls.album_template.format(album_id)
        with request.urlopen(json_address) as response:
            raw = response.read()
            results = json.loads(raw.decode())

        for result in results['data']['images']:
            image_id = result['hash'] + result['ext']
            yield cls.image_template.format(image_id)

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
            yield from cls._get_album(parsed)
        else:
            yield from cls._get_single_image(parsed)


class DeviantArtManager():
    query_url = 'http://backend.deviantart.com/oembed?url={}'

    @classmethod
    def match(cls, url):
        fragment = '/art/'
        parsed = parse.urlparse(url)

        if fragment not in parsed.path or len(parsed.path) <= len(fragment):
            return False

        return parsed.netloc.endswith('deviantart.com')

    @classmethod
    def get_images(cls, url):
        encoded = parse.quote(url, safe="~()*!.'")
        with request.urlopen(cls.query_url.format(encoded)) as response:
            raw = response.read()
            results = json.loads(raw.decode())
        yield results['url']
