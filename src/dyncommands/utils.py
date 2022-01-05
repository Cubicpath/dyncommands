###################################################################################################
#                              MIT Licence (C) 2021 Cubicpath@Github                              #
###################################################################################################
"""Util functions, classes, and attributes for Dynamic Commands"""
from collections.abc import Callable
from typing import Any
from typing import SupportsIndex

import requests

__all__ = (
    'PrivateProxy',
    'get_raw_text',
    'ireplace',
    'DUMMY_FUNC'
)

DUMMY_FUNC: Callable[[...], None] = lambda *args, **kwargs: None


class PrivateProxy:
    """Proxy for private object attributes."""

    # pylint: disable=eval-used
    def __init__(self, o: object,
                 exclude_predicate: Callable[[str, Any], bool] = lambda attr, attr_val: False,
                 include_predicate: Callable[[str, Any], bool] = lambda attr, attr_val: False,
                 starting_underscore_private: bool = True,
                 eval_for_attribute_values:   bool = True):
        """Object that proxies another object, created to prevent methods from accessing private data.

        All attributes starting with _ are by default considered private and are not proxied through.

        :arg o: Object to proxy.
        :arg exclude_predicate: If an attribute name passes the given predicate, it's then considered private.
        :arg include_predicate: If an attribute name passes the given predicate, it will be proxied regardless of private status.
        :arg starting_underscore_private: All attributes starting with an underscore are private if True.
        :arg eval_for_attribute_values: Must be true to work with objects using __slots__.
        """

        for attr in dir(o):
            # Allow use of eval to ensure compatibility with objects using __slots__ as they do not have a __dict__ and attributes must be evaluated
            attr_val:   Any = eval(f'o.{attr}', {'o': o}) if eval_for_attribute_values else vars(o).get(attr)
            is_private: bool = exclude_predicate(attr, attr_val) or (attr.startswith('_') and starting_underscore_private)
            if is_private and include_predicate(attr, attr_val) is False:
                # Don't proxy attr
                continue
            # Proxy attr
            setattr(self, attr, getattr(o, attr))


def get_raw_text(link: str) -> str:
    """Modifies url of common links to get the raw version.

    :param link: Original link to get text from.
    :return: raw text from link.
    """
    headers: dict[str, str] = {'Accept': 'text'}
    sites: tuple[str, ...] = ('gist.github.com', 'rentry.co', 'pastebin.com', 'pastes.io', 'hastebin.com')
    if not link.startswith('https://'):
        link = 'https://' + link.split('://', 1)[-1]
    if 'raw' not in link:
        if True in (site in link for site in sites[:2]):
            link += '/raw'
        elif True in (site in link for site in sites[2:]):
            parts: list[str] = link.removeprefix('https://').split('/')
            parts.insert(1, 'raw')
            link = 'https://' + '/'.join(parts)
    return requests.get(link, headers=headers).text


# https://stackoverflow.com/questions/919056/case-insensitive-replace#answer-4773614
def ireplace(text: str, old_: str, new_: str, count_: SupportsIndex = -1) -> str:
    """Case-insensitive :py:meth:`str.replace` alternative.

    :param text: String to search through.
    :param old_: Case-insensitive substring to look for.
    :param new_: Case-sensitive substring to replace with.
    :param count_: Maximum number of occurrences to replace. -1 (the default value) means replace all occurrences.

    :return: A string with all substrings matching old_ replaced with new_.
    """
    index: int = 0
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
