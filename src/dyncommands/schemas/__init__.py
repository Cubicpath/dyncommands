###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""JSON schema for commands.json files."""
import typing as _t
from abc import ABC
from abc import abstractmethod
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


class SchemaHolder(ABC, dict):
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
    @abstractmethod
    def empty(cls) -> 'SchemaHolder':
        """:return: An empty dict-like object with the required attributes"""
        raise NotImplementedError

    @classmethod
    def validate(cls, data: dict[str, _t.Any]) -> None:
        """Validate the given data with the class' schema structure.

        :param data: JSON data.
        """
        cls._validator.validate(data)


class CommandData(SchemaHolder):
    """Python mapping to command.schema.json objects."""
    __slots__ = ()
    _SCHEMA:    _t.Final[dict[str, _t.Any]] = get_schema('command')
    _validator: _t.Final[Draft7Validator] = Draft7Validator(_SCHEMA)

    @classmethod
    def empty(cls) -> 'CommandData':
        return cls(name='')

    def __init__(self, seq=None, **kwargs) -> None:
        kw = [
            kwargs.pop('name', None),
            kwargs.pop('description', None),
            kwargs.pop('usage', None),
            kwargs.pop('permission', None),
            kwargs.pop('function', None),
            kwargs.pop('children', None),
            kwargs.pop('overridable', None),
            kwargs.pop('disabled', None),
        ]

        super().__init__(seq if seq is not None else {}, **kwargs)
        self.name = kw[0] if kw[0] is not None else self['name']
        if kw[1] is not None: self.description = kw[1]
        if kw[2] is not None: self.usage = kw[2]
        if kw[3] is not None: self.permission = kw[3]
        if kw[4] is not None: self.function = kw[4]
        if kw[5] is not None or self.get('children'):
            self.children = kw[5] if kw[5] is not None else [CommandData(child) for child in self.get('children')]
        if kw[6] is not None: self.overridable = kw[6]
        if kw[7] is not None: self.disabled = kw[7]

    @property
    def name(self) -> str:
        """Uniquely identifies the command to the CommandParser."""
        return self['name']

    @name.setter
    def name(self, value: str):
        self['name'] = value

    @property
    def usage(self) -> str:
        """Usage information (How to use args)."""
        return self.get('usage', '')

    @usage.setter
    def usage(self, value: str):
        self['usage'] = value

    @property
    def description(self) -> str:
        """Description of command."""
        return self.get('description', '')

    @description.setter
    def description(self, value: str):
        self['description'] = value

    @property
    def permission(self) -> int:
        """The permission level the CommandSource requires to run the command."""
        return self.get('permission', 0)

    @permission.setter
    def permission(self, value: int):
        self['permission'] = value

    @property
    def function(self) -> _t.Optional[bool]:
        """Whether there is an associated python module to load."""
        return self.get('function', None)

    @function.setter
    def function(self, value: _t.Optional[bool]):
        self['function'] = value

    @property
    def children(self) -> list['CommandData']:
        """Sub-commands; these are handled by the parent's function. (No associated modules for themselves)."""
        return self.get('children', [])

    @children.setter
    def children(self, value: list['CommandData']):
        self['children'] = value

    @property
    def overridable(self) -> bool:
        """Whether the CommandParser can override any data inside this object (must be manually disabled)."""
        return self.get('overridable', True)

    @overridable.setter
    def overridable(self, value: bool):
        self['overridable'] = value

    @property
    def disabled(self) -> bool:
        """If true still load command, but raise a DisabledError when attempting to execute."""
        return self.get('disabled', False)

    @disabled.setter
    def disabled(self, value: bool):
        self['disabled'] = value


class ParserData(SchemaHolder):
    """Python mapping to parser.schema.json objects."""
    __slots__ = ()
    _SCHEMA:    _t.Final[dict[str, _t.Any]] = SCHEMA
    _validator: _t.Final[Draft7Validator] = Draft7Validator(_SCHEMA)

    @classmethod
    def empty(cls) -> 'ParserData':
        return cls(command_prefix='', commands=[])

    def __init__(self, seq=None, **kwargs) -> None:
        kw = [
            kwargs.pop('commands', None),
            kwargs.pop('command_prefix', None),
        ]

        super().__init__(seq if seq is not None else {}, **kwargs)
        self.commands = kw[0] if kw[0] is not None else [CommandData(command) for command in self['commands']]
        self.command_prefix = kw[1] if kw[1] is not None else self['commandPrefix']

    @property
    def command_prefix(self) -> str:
        """Strings must start with this prefix, otherwise it is ignored. Empty string accepts all."""
        return self['commandPrefix']

    @command_prefix.setter
    def command_prefix(self, value: str):
        self['commandPrefix'] = value

    @property
    def commands(self) -> list[CommandData]:
        """Contains metadata for the stored command modules."""
        return self['commands']

    @commands.setter
    def commands(self, value: list[CommandData]):
        self['commands'] = value
