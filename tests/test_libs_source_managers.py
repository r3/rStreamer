from contextlib import contextmanager
import json
from urllib import parse, request

import pytest

from rStream.libs import source_managers


@pytest.mark.parametrize('test_url,expected_extension', [
    # No extension, should return empty string
    ('http://test.com/', ''),
    # Still no extension, another empty string
    ('http://test.com/foo', ''),
    # This time we have a [bogus] extension, should return the period
    ('http://test.com/foo.bar', '.bar'),
    # Extension should still be returned if arguments are present
    ('http://test.com/foo.bar?baz', '.bar'),
    ('http://test.com/foo.bar?baz=qux', '.bar'),
    ('http://test.com/foo.bar?baz=qux&lorem=ipsem', '.bar'),
])
def test_ext_from_url(test_url, expected_extension):
    assert source_managers.ext_from_url(test_url) == expected_extension


class TestDirectLinkManager():
    @pytest.fixture()
    def manager(self):
        return source_managers.DirectLinkManager()

    def test_config_on_instantiation(self, mocker):
        '''Ensure that the configure method is called on first instantiation'''
        mocker.spy(source_managers.DirectLinkManager, 'configure')
        source_managers.DirectLinkManager()
        source_managers.DirectLinkManager()
        assert source_managers.DirectLinkManager.configure.call_count == 1

    def test_is_configured(self, manager):
        '''Ensure that the _config attribute has a "get" method'''
        assert hasattr(source_managers.DirectLinkManager._config, 'get')

    def test_accepted_extensions_exists(self, manager):
        '''Ensure that accepted_extensions is populated on instantiation'''
        assert manager.accepted_extensions

    # Note that we monkeypatch DirectLinkManager.accepted_extensions
    # to allow only '.foo'
    @pytest.mark.parametrize('url,is_match', [
        ('http://test.com', False),
        ('http://test.com/', False),
        # This one ends in '.foo' and should match
        ('http://test.com/test.foo', True),
        ('http://test.com/test.bar', False),
        # It should still match if arguments exist
        ('http://test.com/test.foo?bar=baz', True),
        ('http://test.com/test.foo?bar=baz&qux', True),
    ])
    def test_match(self, monkeypatch, url, is_match):
        '''Sends a variety of URLs to the match method. Expects ".foo" ext'''
        monkeypatch.setattr(source_managers.DirectLinkManager,
                            'accepted_extensions',
                            ['.foo'])
        assert source_managers.DirectLinkManager.match(url) == is_match

    def test_valid_get_images(self, monkeypatch, manager):
        '''DirectLinkManager only returns the passed url, in a generator'''
        monkeypatch.setattr(source_managers.DirectLinkManager,
                            'accepted_extensions',
                            ['.foo'])
        url = 'http://test.com/test.foo'
        results = manager.get_images(url)
        assert next(results) == url
        with pytest.raises(StopIteration):
            next(results)

    def test_invalid_get_images(self, manager):
        '''If the url does not link to an image, the results will be empty'''
        url = 'http://test.com/'
        results = manager.get_images(url)
        with pytest.raises(StopIteration):
            next(results)


class TestGfycatManager():
    @pytest.fixture()
    def manager(self):
        return source_managers.GfycatManager()

    @pytest.mark.parametrize('url,is_match', [
        # While the domain matches, there's no image referenced
        ('http://gfycat.com/', False),
        # Domain doesn't match
        ('http://test.com/', False),
        # These are potentially albums or images
        ('http://gfycat.com/Foo', True),
        ('http://giant.gfycat.com/Foo.gif', True),
        # But this one is invalid
        ('http://giant.gfycat.com/Foo', False),
    ])
    def test_match(self, manager, url, is_match):
        assert manager.match(url) == is_match

    # Note that `None` is used as a sentinel for an empty iterable
    # the get_images methods should be generator-like.
    @pytest.mark.parametrize('url,image_url', [
        # We're pulling the GIF from our links, though this may change
        ('http://gfycat.com/Foobar',
            'http://giant.gfycat.com/Foobar.gif'),
        # No images referenced
        ('http://gfycat.com/', None),
        # Again, pulling GIF files, even from direct references to alt formats
        ('http://giant.gfycat.com/Foo.webm',
            'http://giant.gfycat.com/Foo.gif'),
        # The old identity
        ('http://giant.gfycat.com/Foo.gif',
            'http://giant.gfycat.com/Foo.gif'),
    ])
    def test_get_images(self, manager, url, image_url):
        results = manager.get_images(url)

        if image_url is None:
            with pytest.raises(StopIteration):
                next(results)
        else:
            assert next(results) == image_url
            with pytest.raises(StopIteration):
                next(results)


class TestImgurManager():
    @pytest.fixture()
    def manager(self):
        return source_managers.ImgurManager()

    @pytest.mark.parametrize('url,is_match', [
        # Domain matches, but no image or album referenced
        ('http://imgur.com/', False),
        ('http://i.imgur.com/', False),
        # Domain doesn't match, obvious failures should still be tested
        ('http://test.com/', False),
        # These ones link to either an image or album
        ('http://imgur.com/Foo', True),
        ('http://imgur.com/a/Foo', True),
    ])
    def test_match(self, manager, url, is_match):
        assert manager.match(url) == is_match

    @pytest.mark.parametrize('url,image', [
        # We don't bother check the extension for imgur links, clean results
        ('http://imgur.com/foo.bar', 'http://i.imgur.com/foo.bar'),
        # Identity should work
        ('http://i.imgur.com/foo.bar', 'http://i.imgur.com/foo.bar'),
        # Even ugly urls should wok
        ('http://i.imgur.com/foo.bar/', 'http://i.imgur.com/foo.bar'),
    ])
    def test__get_single_image(self, manager, url, image):
        parsed = parse.urlparse(url)
        result = manager._get_single_image(parsed)
        assert next(result) == image

    @pytest.mark.parametrize('url,images', [
        # Albums should be expected to return several results
        ('http://imgur.com/a/foo', [
            'http://i.imgur.com/1.ext',
            'http://i.imgur.com/2.ext',
            'http://i.imgur.com/3.ext',
        ]),
        # Even albums with ugly urls
        ('http://i.imgur.com/a/foo/', [
            'http://i.imgur.com/1.ext',
            'http://i.imgur.com/2.ext',
            'http://i.imgur.com/3.ext',
        ]),

    ])
    def test__get_album(self, monkeypatch, manager, url, images):
        class MockResponse():
            def read(*args, **kwargs):
                result = json.dumps({
                    'data': {
                        'images': [
                            {
                                'hash': '1',
                                'ext': '.ext'
                            },
                            {
                                'hash': '2',
                                'ext': '.ext'
                            },
                            {
                                'hash': '3',
                                'ext': '.ext'
                            },
                        ]
                    }
                })

                return bytes(result, 'utf8')

        @contextmanager
        def mock_urlopen(*args, **kwargs):
            yield MockResponse()

        monkeypatch.setattr(request, 'urlopen', mock_urlopen)

        results = manager.get_images(url)

        if images is None:
            with pytest.raises(StopIteration):
                next(results)
        else:
            result = list(manager.get_images(url))
            assert result == images

    def test_get_images(self, mocker, monkeypatch, manager):
        '''Ensures that get_images routes properly to support methods'''
        mocker.spy(source_managers.ImgurManager, '_get_single_image')
        image_url = 'http://i.imgur.com/Foo.bar'
        next(manager.get_images(image_url))
        assert source_managers.ImgurManager._get_single_image.call_count == 1

        monkeypatch.setattr(source_managers.ImgurManager,
                            '_get_album',
                            lambda x: x)
        mocker.spy(source_managers.ImgurManager, '_get_album')
        album_url = 'http://imgur.com/a/Foo'
        next(manager.get_images(album_url))
        assert source_managers.ImgurManager._get_album.call_count == 1


class TestDeviantArtManager():
    @pytest.fixture()
    def manager(self):
        return source_managers.DeviantArtManager()

    @pytest.mark.parametrize('url,is_match', [
        # Obviously not a deviantart image
        ('http://foo.bar', False),
        # These one is a link to deviantart, but no image specified; no match
        ('http://deviantart.com/', False),
        ('http://deviantart.com/art/', False),
        ('http://foo.deviantart.com/', False),
        ('http://foo.deviantart.com/art/', False),
        # This lacks the '/art/' path and would 404 on request
        ('http://foo.deviantart.com/bar', False),
        # This one is valid
        ('http://foo.deviantart.com/art/bar-123456', True),
        # Even without the username in the domain, it should work
        # This URL points to the same resource as above
        ('http://deviantart.com/art/bar-123456', True),
    ])
    def test_match(self, manager, url, is_match):
        assert manager.match(url) == is_match

    @pytest.mark.parametrize('url,image', [
        ('http://foo.deviantart.com/art/bar-123456',
         'http://pre00.deviantart.net/foo/th/pre/f/0000/000/0/f/bar.baz'),
    ])
    def test_get_images(self, monkeypatch, manager, url, image):
        class MockResponse():
            def read(*args, **kwargs):
                result = json.dumps({
                    'url': ('http://pre00.deviantart.net/foo/'
                            'th/pre/f/0000/000/0/f/bar.baz'),
                })

                return bytes(result, 'utf8')

        @contextmanager
        def mock_urlopen(*args, **kwargs):
            yield MockResponse()

        monkeypatch.setattr(request, 'urlopen', mock_urlopen)

        results = manager.get_images(url)

        if image is None:
            with pytest.raises(StopIteration):
                next(results)
        else:
            assert next(results) == image
            with pytest.raises(StopIteration):
                next(results)
