###################################################################################################
#                              MIT Licence (C) 2021 Cubicpath@Github                              #
###################################################################################################
# noinspection PyUnresolvedReferences
# Name: unrestricted
from pathlib import Path

import requests

from dyncommands.utils import get_raw_text


def command(*_, **__):
    text = get_raw_text('https://gist.github.com/Cubicpath/8fc611ca67bf2d17e03b4766a816596a')
    path = Path(__file__).parent / 'test.txt'
    with path.open(mode='w', encoding='utf8') as file:
        file.write(text)
    with path.open(mode='r', encoding='utf8') as file:
        return file.read()
