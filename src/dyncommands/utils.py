###################################################################################################
#                              MIT Licence (C) 2021 Cubicpath@Github                              #
###################################################################################################
"""Utils for Dynamic Commands"""
from collections.abc import Callable
from typing import SupportsIndex

__all__ = (
    'PrivateProxy',
    'get_raw_text',
    'ireplace',
    'DUMMY_FUNC'
)

import requests

DUMMY_FUNC = lambda *args, **kwargs: None


class PrivateProxy:
    """Proxy for private object attributes."""

    def __init__(self, o: object,
                 exclude_predicate: Callable[[str], bool] = lambda attr: False,
                 include_predicate: Callable[[str], bool] = lambda attr: False,
                 starting_underscore_private: bool = True):
        """Object that proxies another object, created to prevent methods from accessing private data.

        All attributes starting with _ are by default considered private and are not proxied through.

        :arg o: Object to proxy.
        :arg exclude_predicate: If an attribute name passes the given predicate, it's then considered private.
        :arg include_predicate: If an attribute name passes the given predicate, it will be proxied regardless of private status.
        :arg starting_underscore_private: All attributes starting with an underscore are private if True.
        """

        for attr in dir(o):
            if include_predicate(attr) is False and ((attr.startswith('_') and starting_underscore_private) or exclude_predicate(attr) is True):
                # Don't proxy attr
                continue
            # Proxy attr
            setattr(self, attr, getattr(o, attr))


def get_raw_text(link: str) -> str:
    """Modifies url of common links to get the raw version.
    :param link: Original link to get text from.
    :return: raw text from link.
    """
    headers = {'Accept': 'text'}
    if not link.startswith('https://'):
        link = 'https://' + link.split('://', 1)[-1]
    if 'raw' not in link:
        if 'gist.github.com' in link or 'rentry.co' in link:
            link += '/raw'
        elif 'pastebin.com' in link or 'hastebin.com' in link:
            new = link.removeprefix('https://').split('/')
            new.insert(1, 'raw')
            link = 'https://' + '/'.join(new)
    text = requests.get(link, headers=headers).text
    return text


# https://stackoverflow.com/questions/919056/case-insensitive-replace#answer-4773614
def ireplace(text: str, old_: str, new_: str, count_: SupportsIndex = -1) -> str:
    """Case-insensitive str.replace alternative.
    :param text: String to search through.
    :param old_: Case-insensitive substring to look for.
    :param new_: Case-sensitive substring to replace with.
    :param count_: Maximum number of occurrences to replace. -1 (the default value) means replace all occurrences.

    :return: A string with all substrings matching __old replaced with __new.
    """
    index = 0
    if not old_:
        return text.replace('', new_)
    if text.lower() == old_.lower() and count_.__index__() != 0:
        return new_
    while index < len(text) and count_.__index__() < 0:
        index_l = text.lower().find(old_.lower(), index)
        if index_l == -1:
            return text
        text = text[:index_l] + new_ + text[index_l + len(old_):]
        index = index_l + len(new_)
    return text
