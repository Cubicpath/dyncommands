###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Utils for the dyncommands.schemas package"""
from importlib.resources import read_text
from json import loads
from typing import Any

__all__ = (
    'get_schema',
)


def get_schema(name: str) -> dict[str, Any]:
    """Returns the JSON representation of a schema resource.

    :raises FileNotFoundError: If name given does not exist as a resource.
    :raises ValueError: If __package__ of this module is None.
    """
    return loads(read_text(__package__ or '', f'{name}.schema.json'))
