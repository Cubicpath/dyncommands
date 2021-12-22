###################################################################################################
#                              MIT Licence (C) 2021 Cubicpath@Github                              #
###################################################################################################
"""JSON schema for commands.json files."""
import json
from pathlib import Path
from typing import Any
from typing import Optional

from jsonschema import Draft7Validator

__all__ = (
    'CommandData',
    'SCHEMA'
)


with (Path(__file__).parent / 'schemas/commands.json').open(mode='r', encoding='utf8') as schema:
    SCHEMA: dict[str, Any] = json.loads(schema.read())
    del schema


class CommandData(dict):
    __slots__ = ('commands', 'commandPrefix')
    SCHEMA = SCHEMA

    Draft7Validator.check_schema(SCHEMA)
    Validator = Draft7Validator(SCHEMA)

    class SchemaCommand(dict):
        __slots__ = ('children', 'description', 'disabled', 'function', 'name', 'overridable', 'permission', 'usage')
        SCHEMA: dict[str, Any]
        Validator: Draft7Validator

        def __init__(self, seq=None, **kwargs):
            super().__init__(seq, **kwargs)
            self.name:          str = self['name']
            self.description:   str = self.get('description', '')
            self.usage:         str = self.get('usage', '')
            self.permission:    int = self.get('permission', 0)
            self.function:      Optional[bool] = self.get('function', False)
            self.children:      list[CommandData.SchemaCommand] = [CommandData.SchemaCommand(child) for child in self.get('children', [])]
            self.overridable:   bool = self.get('overridable', True)
            self.disabled:      bool = self.get('disabled', False)

        @classmethod
        def validate(cls, data) -> None:
            cls.Validator.validate(data)

    SchemaCommand.SCHEMA = SCHEMA['definitions']['command']
    SchemaCommand.Validator = Draft7Validator(SchemaCommand.SCHEMA)

    def __init__(self, seq=None, **kwargs):
        super().__init__(seq, **kwargs)
        self.validate(self)

        self['commands'] = [self.SchemaCommand(command) for command in self['commands']]
        self.commands:      list[CommandData.SchemaCommand] = self['commands']
        self.commandPrefix: str = self['commandPrefix']

    @classmethod
    def validate(cls, data) -> None:
        cls.Validator.validate(data)
