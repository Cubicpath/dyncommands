###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""JSON schema for commands.json files."""
import collections.abc as _c
import typing as _t
from abc import ABC
from abc import abstractmethod
from importlib.resources import read_text as _read
from json import loads as _loads

from jsonschema import Draft7Validator
from jsonschema import Validator

from .constants import *

__all__ = (
    'CommandData',
    'get_schema',
    'ParserData',
    'SCHEMA',
    'SchemaHolder',
)


def get_schema(name: str) -> dict[str, _t.Any]:
    """Returns the JSON representation of a schema resource.

    :raises ValueError: If __package__ is None
    """
    return _loads(_read(__package__ or '', f'{name}.schema.json'))


SCHEMA: _t.Final[dict[str, _t.Any]] = get_schema('parser')


class SchemaHolder(ABC, dict):
    """Generic dictionary that represents a JSON Schema. Draft-07 by default.

    All attributes lookups that are not already defined will return the respective key value. Ex::

        schema_holder.pop -> schema_holder.pop (inherited from dict.pop)
        schema_holder._SCHEMA -> schema_holder._SCHEMA
        schema_holder.array -> schema_holder.get('array', <SCHEMA DEFAULT>)
        schema_holder.z123 -> schema_holder.get('z123', <SCHEMA DEFAULT>)

    It is recommended for all subclasses to define __slots__.
    """
    __slots__ = ()
    __REF_CACHE:     dict[str, type]
    _META_VALIDATOR: Validator = Draft7Validator         # jsonschema Validator to use
    _SCHEMA:         dict[str, _t.Any] = NotImplemented  # Must be overridden
    _validator:      Validator = NotImplemented          # Auto-built from _META_VALIDATOR and _SCHEMA if not defined

    # # # # # # # # # # #  CLASS METHODS

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        if cls._SCHEMA is NotImplemented:
            raise NotImplementedError(f'{cls.__name__}._SCHEMA must be implemented when extending SchemaHolder.')

        Draft7Validator.check_schema(SCHEMA)
        if cls._validator is NotImplemented:
            cls._validator = cls._META_VALIDATOR(cls._SCHEMA)

        cls.__REF_CACHE = {}

    @classmethod
    @abstractmethod
    def empty(cls) -> 'SchemaHolder':
        """:return: An empty dict-like object with required attributes"""
        raise NotImplementedError()

    @classmethod
    def validate(cls, data: dict[str, _t.Any]) -> None:
        """Validate the given data with the class' schema structure.

        :param data: JSON data.
        """
        cls._validator.validate(data)

    # # # # # # # # # # #  INSTANCE METHODS

    def __dir__(self) -> _c.Iterable[str]:
        return sorted(set(
            tuple(dir(type(self))) + self.__slots__ + tuple(self.keys()) + tuple(self._SCHEMA.get('properties', {}).keys())
        ))

    def __getattr__(self, key: str) -> _t.Any:
        """Get a defined attribute or dictionary key.

        :return: An object attribute if defined, else an internal key value. Key must be in schema.
        :raises KeyError: Key not defined in the schema properties.
        """
        if key in dir(type(self)):
            return super().__getattribute__(key)

        value: _t.Any = self.get(key, NOT_FOUND)

        if value is NOT_FOUND:
            if key not in self._SCHEMA.get('properties', ()):
                raise KeyError(f'Key "{key}" does not conform to _SCHEMA and is not defined.')

            # Get default value from schema
            value = self._SCHEMA['properties'][key].get('default')

        props: dict = self._SCHEMA.get('properties', {}).get(key, NOT_FOUND)
        if props is not NOT_FOUND:
            value = self._conform_value(value, props)

        return value

    def __setattr__(self, key: str, value: _t.Any) -> None:
        """Sets an object attribute if defined, else sets an internal key value. Key must be in schema.

        :raises KeyError: Key not defined in the schema properties.
        """
        if key in dir(type(self)):
            return super().__setattr__(key, value)

        if key not in self._SCHEMA.get('properties', {}):
            raise KeyError(f'Key "{key}" does not conform to _SCHEMA and cannot be set.')

        props: dict = self._SCHEMA.get('properties', {}).get(key, NOT_FOUND)
        if props is not NOT_FOUND:
            value = self._conform_value(value, props)

        self[key] = value

    def __delattr__(self, key: str) -> None:
        """Deletes an object attribute if defined, else pops an internal key value. Key must not be required.

        :raises KeyError: Key is either required or not defined in schema properties.
        """
        if key in dir(type(self)):
            return super().__delattr__(key)

        if key not in self._SCHEMA.get('properties', {}):
            raise KeyError(f'Key "{key}" does not conform to _SCHEMA and cannot be deleted.')

        if key in self._SCHEMA.get('required', ()):
            raise KeyError(f'You cannot delete required key "{key}".')

        self.pop(key)

    def _cache_ref_schema(self, ref_path: str) -> None:
        """Create a new schema holder using the definition found from the ref_path, then cache it."""
        schema_class: type
        definition: dict[str, _t.Any] = self._SCHEMA

        for obj in ref_path.split('/')[1:]:
            definition = definition[obj]
        if definition.get('$ref', '').replace('/', '') == '#':
            definition = self._SCHEMA

        # Create a new schema holder using the definition found from the $ref value
        class CachedSchema(SchemaHolder):
            """Dynamically generated schema class meant to be cached for later use."""
            _SCHEMA = definition

            @classmethod
            def empty(cls) -> 'CachedSchema':
                return cls()

        schema_class = CachedSchema
        self.__REF_CACHE[ref_path] = schema_class

    def _conform_value(self, value, props) -> 'SchemaHolder':
        """Automatically translate JSON objects and arrays with a $ref schema to SchemaHolders"""
        ref_type: int = 1 if ('$ref' in props) else 2 if ('$ref' in props.get('items', ())) else 0
        if ref_type and not isinstance(value, SchemaHolder):
            ref_path: str = props['$ref'] if (ref_type == 1) else (props['items']['$ref'] if (ref_type == 2) else None)
            schema_class: type

            if ref_path.replace('/', '') == '#':
                schema_class = self.__class__
            elif ref_path in self.__REF_CACHE:
                # Get cached class for reference
                schema_class = self.__REF_CACHE[ref_path]
            else:
                self._cache_ref_schema(ref_path)
                schema_class = self.__REF_CACHE[ref_path]

            value = schema_class(value) if ref_type == 1 else [schema_class(item) for item in value] if ref_type == 2 else None
        return value


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
            kwargs.pop('name',        NOT_FOUND),
            kwargs.pop('description', NOT_FOUND),
            kwargs.pop('usage',       NOT_FOUND),
            kwargs.pop('permission',  NOT_FOUND),
            kwargs.pop('function',    NOT_FOUND),
            kwargs.pop('children',    NOT_FOUND),
            kwargs.pop('overridable', NOT_FOUND),
            kwargs.pop('disabled',    NOT_FOUND),
        ]

        super().__init__(seq if seq is not None else {}, **kwargs)
        self.name = kw[0] if kw[0] is not NOT_FOUND else self['name']
        if kw[1] is not NOT_FOUND: self.description: str = kw[1]
        if kw[2] is not NOT_FOUND: self.usage:       str = kw[2]
        if kw[3] is not NOT_FOUND: self.permission:  int = kw[3]
        if kw[4] is not NOT_FOUND: self.function:    _t.Optional[bool] = kw[4]
        if kw[5] is not NOT_FOUND or self.get('children'):
            self.children = kw[5] if kw[5] is not NOT_FOUND else [CommandData(child) for child in self.get('children')]
        if kw[6] is not NOT_FOUND: self.overridable = kw[6]
        if kw[7] is not NOT_FOUND: self.disabled = kw[7]


class ParserData(SchemaHolder):
    """Python mapping to parser.schema.json objects."""
    __slots__ = ()
    _SCHEMA:    _t.Final[dict[str, _t.Any]] = SCHEMA
    _validator: _t.Final[Draft7Validator] = Draft7Validator(_SCHEMA)

    @classmethod
    def empty(cls) -> 'ParserData':
        return cls(commandPrefix='', commands=[])

    def __init__(self, seq=None, **kwargs) -> None:
        kw = [
            kwargs.pop('commandPrefix', NOT_FOUND),
            kwargs.pop('commands',      NOT_FOUND),
        ]

        super().__init__(seq if seq is not None else {}, **kwargs)
        self.commandPrefix = kw[0] if kw[0] is not NOT_FOUND else self['commandPrefix']
        self.commands = kw[1] if kw[1] is not NOT_FOUND else [CommandData(command) for command in self.get('commands')]
