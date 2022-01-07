###################################################################################################
#                              MIT Licence (C) 2021 Cubicpath@Github                              #
###################################################################################################
"""JSON schema for commands.json files."""
import typing as _t
from importlib.resources import read_text as _read
from json import loads as _loads

from jsonschema import Draft7Validator

__all__ = (
    'CommandData',
    'get_schema',
    'ParserData',
    'SCHEMA',
    'SchemaHolder',
)


def get_schema(name: str) -> dict[str, _t.Any]:
    """Returns the JSON representation of a schema resource."""
    return _loads(_read('dyncommands.schemas', f'{name}.schema.json'))


SCHEMA: _t.Final[dict[str, _t.Any]] = get_schema('parser')


class SchemaHolder(dict):
    """Generic dictionary that represents a JSON Schema. Draft-07 by default."""
    __slots__ = ()
    _META_VALIDATOR = Draft7Validator
    _SCHEMA = NotImplemented
    _validator = NotImplemented

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls._SCHEMA is NotImplemented:
            raise NotImplementedError(f'{cls.__name__}._SCHEMA must be implemented when extending SchemaHolder.')

        Draft7Validator.check_schema(SCHEMA)
        if cls._validator is NotImplemented:
            cls._validator = cls._META_VALIDATOR(cls._SCHEMA)

    @classmethod
    def validate(cls, data: dict[str, _t.Any]) -> None:
        """Validate the given data with the class' schema structure.

        :param data: JSON data.
        """
        cls._validator.validate(data)


class CommandData(SchemaHolder):
    """Python mapping to command.schema.json objects."""
    __slots__ = ('children', 'description', 'disabled', 'function', 'name', 'overridable', 'permission', 'usage')
    _SCHEMA:    _t.Final[dict[str, _t.Any]] = get_schema('command')
    _validator: _t.Final[Draft7Validator] = Draft7Validator(_SCHEMA)

    def __init__(self, seq=None, **kwargs) -> None:
        super().__init__(seq if seq is not None else {}, **kwargs)
        self.name:          str = kwargs.pop('name', self['name'])
        self.description:   str = kwargs.pop('description', self.get('description', ''))
        self.usage:         str = kwargs.pop('usage', self.get('usage', ''))
        self.permission:    int = kwargs.pop('permission', self.get('permission', 0))
        self.function:      _t.Optional[bool] = kwargs.pop('function', self.get('function', None))
        self.children:      list[CommandData]
        if kwargs.get('children') or self.get('children'):
            self['children'] = kwargs.pop('children', [CommandData(child) for child in self.get('children')])
            self.children = self['children']
        else:
            self.children = []
        self.overridable:   bool = kwargs.pop('overridable', self.get('overridable', True))
        self.disabled:      bool = kwargs.pop('disabled', self.get('disabled', False))


class ParserData(SchemaHolder):
    """Python mapping to parser.schema.json objects."""
    __slots__ = ('commands', 'command_prefix')
    _SCHEMA:    _t.Final[dict[str, _t.Any]] = SCHEMA
    _validator: _t.Final[Draft7Validator] = Draft7Validator(_SCHEMA)

    def __init__(self, seq=None, **kwargs) -> None:
        super().__init__(seq if seq is not None else {}, **kwargs)
        self['commands'] = kwargs.pop('commands', [CommandData(command) for command in self['commands']])
        self.commands:       list[CommandData] = self['commands']
        self.command_prefix: str = kwargs.pop('commandPrefix', self['commandPrefix'])
