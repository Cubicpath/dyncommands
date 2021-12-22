###################################################################################################
#                              MIT Licence (C) 2021 Cubicpath@Github                              #
###################################################################################################
"""JSON schema for commands.json files."""
import json
from pathlib import Path
from typing import Any
from typing import Optional

from jsonschema import Draft7Validator
from jsonschema import validate

__all__ = (
    "CommandData",
)


class CommandData(dict):
    SCHEMA: dict[str, Any]

    with (Path(__file__).parent / 'schemas/commands.json').open(mode='r', encoding='utf8') as schema:
        SCHEMA = json.loads(schema.read())
        del schema

    Draft7Validator.check_schema(SCHEMA)

    class SchemaCommand(dict):
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

    def __init__(self, seq=None, **kwargs):
        super().__init__(seq, **kwargs)
        self.validate(self)

        self['commands'] = [self.SchemaCommand(command) for command in self['commands']]
        self.commandPrefix: str = self['commandPrefix']
        self.commands:      list[CommandData.SchemaCommand] = self['commands']

    @classmethod
    def validate(cls, data) -> None:
        validate(data, schema=cls.SCHEMA)
