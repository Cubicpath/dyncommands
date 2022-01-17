###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Tests for the utils.py module."""
import sys
import unittest
from pathlib import Path

from dyncommands._version import _stringify as version_stringify
from dyncommands.utils import *

# Boilerplate to allow running script directly.
if __name__ == '__main__' and __package__ is None: sys.path.insert(1, str(Path(__file__).resolve().parent.parent)); __package__ = 'tests'


# noinspection PyUnresolvedReferences
class TestPrivateProxy(unittest.TestCase):
    """Tests for PrivateProxy."""

    def test_public_attrs(self) -> None:
        """Inclusion of public attrs"""
        # Proxy a str object; public attributes proxied
        proxy = PrivateProxy('foo')
        self.assertRaises(TypeError, lambda: proxy + 'bar')
        self.assertTrue(proxy.isalpha())
        self.assertTrue(proxy.isalnum())
        self.assertTrue(proxy.isascii())

    def test_exclude_attrs(self) -> None:
        """Exclusion of all attributes"""
        # Proxy a str object; excludes ALL attributes from being proxied
        proxy = PrivateProxy('foo', exclude_predicate=lambda *args, **kwargs: True)
        self.assertNotIn(True, (not a.startswith('_') for a in dir(proxy)))
        self.assertNotIn(True, (a.startswith('_') and not a.startswith('__') for a in dir(proxy)))

    def test_include_attr(self) -> None:
        """Inclusion of normally excluded attrs"""
        # Proxy a str object; proxies additional dunder methods __add__, __mul__ and __str__
        proxy = PrivateProxy('foo', include_predicate=lambda attr, *_: attr in ('__add__', '__mul__', '__str__'))
        self.assertNotEqual('foo', proxy)
        self.assertEqual('foo', proxy.__str__())
        self.assertEqual('foobar', proxy.__str__() + 'bar')
        self.assertEqual('foobar', proxy.__add__('bar'))
        self.assertEqual('foo' * 5 + 'bar', proxy.__mul__(5) + 'bar')
        self.assertRaises(TypeError, proxy.__ge__)
        self.assertRaises(TypeError, proxy.__le__)

    def test_remove_single_attr(self) -> None:
        """Exclusion of single attr"""
        proxy = PrivateProxy('foo')
        # Remove isalpha attribute from existing proxy object
        proxy = PrivateProxy(proxy, exclude_predicate=lambda attr, *_: attr == 'isalpha')
        self.assertRaises(AttributeError, lambda: proxy.isalpha())
        self.assertTrue(proxy.isalnum())
        self.assertTrue(proxy.isascii())

        # No changes, attribute already removed
        proxy = PrivateProxy(proxy, include_predicate=lambda attr, *_: attr == 'isalpha')
        self.assertRaises(AttributeError, lambda: proxy.isalpha())


class TestFunctions(unittest.TestCase):
    """Tests for utils functions."""

    def setUp(self) -> None:
        self.test_string = 'sm oefOWFMG)#0i30t93jf ()I#jf9oKS9 k( j3jr 9J(RK '

    def test_get_raw_text(self) -> None:
        """Getting raw content of links"""
        gist_test = 'https://gist.github.com/Cubicpath/7cf95577019bac28868e9420616d0df9'
        pastebin_test = 'https://pastebin.com/GiFyqGLS'
        self.assertEqual(get_raw_text(gist_test), self.test_string)
        self.assertEqual(get_raw_text(gist_test.removeprefix('https://')), self.test_string)
        self.assertEqual(get_raw_text(gist_test.replace('https', 'http')), self.test_string)
        self.assertEqual(get_raw_text(pastebin_test), self.test_string)

    def test_ireplace(self) -> None:
        """ireplace comparisons and str.replace parity"""
        # Empty strings
        self.assertEqual(self.test_string, ireplace(self.test_string, '', ''))
        self.assertEqual(self.test_string, self.test_string.replace('', ''))

        # Whitespace strings
        self.assertEqual(self.test_string, ireplace(self.test_string, ' ', ' '))
        self.assertEqual(self.test_string, self.test_string.replace(' ', ' '))

        # Replace self with self
        self.assertEqual(self.test_string, ireplace(self.test_string, self.test_string, self.test_string))
        self.assertEqual(self.test_string, self.test_string.replace(self.test_string, self.test_string))
        self.assertEqual(self.test_string, ireplace(self.test_string, self.test_string.swapcase(), self.test_string))

        # Replace self with empty string
        self.assertEqual('', ireplace(self.test_string, self.test_string, ''))
        self.assertEqual('', ireplace(self.test_string, self.test_string.swapcase(), ''))
        self.assertEqual('', ireplace(self.test_string.swapcase(), self.test_string, ''))

        # Replace substrings
        self.assertEqual(self.test_string[6:], ireplace(self.test_string, 'SM OEF', ''))  # Replace prefix with empty string
        self.assertEqual(ireplace(self.test_string, 'Sm oEf', ''), ireplace(self.test_string, 'SM OEF', ''))  # Parity between Case-swapped replace
        self.assertEqual(self.test_string.replace('', 'sm oef'), ireplace(self.test_string, '', 'sm oef'))  # Replicate str.replace behavior for empty string

    def test_version_stringify(self) -> None:
        """_version.py stringify checks"""
        self.assertEqual(version_stringify(2021, 9), '2021.9')
        self.assertEqual(version_stringify(0, 3, 2, 'beta'), '0.3.2b')
        self.assertEqual(version_stringify(1, 0, 0, 'release'), '1.0')
        self.assertEqual(version_stringify(3, 10, 0, 'candidate', 0), '3.10rc')
        self.assertEqual(version_stringify(3, 9, 1, 'alpha', 3), '3.9.1a3')
        self.assertEqual(version_stringify(3, 9, 1, dev=2), '3.9.1.dev2')
        self.assertEqual(version_stringify(20, 45, 0, dev=2, dev_sep='_', dev_post=1, post_spelling='r'), '20.45_dev2.r1')
        self.assertEqual(version_stringify(3, 9, 2, 'preview', 3, post=0, post_implicit=True, dev=5), '3.9.2pre3-0.dev5')
        self.assertEqual(version_stringify(1, 0, local='ubuntu', local_ver=2, local_ver_sep='-'), '1.0+ubuntu-2')
        self.assertRaises(TypeError, version_stringify, self.test_string)
        kwargs = {}
        test_keys = (
            'releaselevel', 'post_spelling', 'local_ver_sep', 'pre_sep', 'pre_ver_sep',
            'post_sep', 'post_ver_sep', 'dev_sep', 'dev_post_sep', 'dev_post_ver_sep'
        )
        for kwarg in test_keys:
            kwargs.update({kwarg: '+11_39/8 \08k.f39-h$f'})
            self.assertRaises(ValueError, version_stringify, 1, 0, **kwargs)
            kwargs.clear()
        for kwarg in ('major', 'minor', 'micro', 'local_ver, post, dev, dev_post'):
            kwargs.update({kwarg: 'string'})
            self.assertRaises(TypeError, version_stringify, 1, 0, **kwargs)


if __name__ == '__main__':
    unittest.main()
