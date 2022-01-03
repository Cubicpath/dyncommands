###################################################################################################
#                              MIT Licence (C) 2021 Cubicpath@Github                              #
###################################################################################################
"""JSON schema for commands.json files."""
import json
from pathlib import Path
from typing import Any
from typing import Final
from typing import Optional

from jsonschema import Draft7Validator

__all__ = (
    'CommandData',
    'ParserData',
    'SCHEMA'
)

with (Path(__file__).parent / 'schemas/commands.schema.json').open(mode='r', encoding='utf8') as _schema:
    SCHEMA: Final[dict[str, Any]] = json.loads(_schema.read())
    Draft7Validator.check_schema(SCHEMA)
    del _schema


class CommandData(dict):
    """Python mapping to command.schema.json objects."""
    __slots__ = ('children', 'description', 'disabled', 'function', 'name', 'overridable', 'permission', 'usage')
    _SCHEMA:    Final[dict[str, Any]] = SCHEMA['definitions']['command']
    _VALIDATOR: Final[Draft7Validator] = Draft7Validator(_SCHEMA)

    def __init__(self, seq=None, **kwargs) -> None:
        super().__init__(seq if seq is not None else {}, **kwargs)
        self.name:          str = kwargs.pop('name', self['name'])
        self.description:   str = kwargs.pop('description', self.get('description', ''))
        self.usage:         str = kwargs.pop('usage', self.get('usage', ''))
        self.permission:    int = kwargs.pop('permission', self.get('permission', 0))
        self.function:      Optional[bool] = kwargs.pop('function', self.get('function', None))
        self.children:      list[CommandData]
        if kwargs.get('children') or self.get('children'):
            self['children'] = kwargs.pop('children', [CommandData(child) for child in self.get('children')])
            self.children = self['children']
        else:
            self.children = []
        self.overridable:   bool = kwargs.pop('overridable', self.get('overridable', True))
        self.disabled:      bool = kwargs.pop('disabled', self.get('disabled', False))

    @classmethod
    def validate(cls, data: dict[str, Any]) -> None:
        """Validate the given data with the class' schema structure.

        :param data: JSON data.
        """
        cls._VALIDATOR.validate(data)


class ParserData(dict):
    """Python mapping to commands.schema.json objects."""
    __slots__ = ('commands', 'command_prefix')
    _SCHEMA:    Final[dict[str, Any]] = SCHEMA
    _VALIDATOR: Final[Draft7Validator] = Draft7Validator(_SCHEMA)

    def __init__(self, seq=None, **kwargs) -> None:
        super().__init__(seq if seq is not None else {}, **kwargs)
        self['commands'] = kwargs.pop('commands', [CommandData(command) for command in self['commands']])
        self.commands:       list[CommandData] = self['commands']
        self.command_prefix: str = kwargs.pop('commandPrefix', self['commandPrefix'])

    @classmethod
    def validate(cls, data: dict[str, Any]) -> None:
        """Validate the given data with the class' schema structure.

        :param data: JSON data.
        """
        cls._VALIDATOR.validate(data)
