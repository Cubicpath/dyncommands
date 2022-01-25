###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Python representation of JSON objects."""
from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Final
from typing import Optional
from warnings import warn

from jsonschema import Draft7Validator
from jsonschema import Validator

from .constants import NOT_FOUND
from .constants import SCHEMA_DEFAULT
from .utils import get_schema

__all__ = (
    'CommandData',
    'ParserData',
    'SCHEMA',
    'SchemaHolder',
)


SCHEMA: Final[dict[str, Any]] = get_schema('parser')


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
    __REF_CACHE: dict[str, type]
    _META_VALIDATOR: Validator = Draft7Validator  # jsonschema Validator to use
    _SCHEMA: dict[str, Any] = NotImplemented  # Must be overridden
    _validator: Validator = NotImplemented  # Auto-built from _META_VALIDATOR and _SCHEMA if not defined
    _warned: bool = False  # Set to true to disable first-time warnings

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
    def validate(cls, data: dict[str, Any]) -> None:
        """Validate the given data with the class' schema structure.

        :param data: JSON data.
        """
        cls._validator.validate(data)

    # # # # # # # # # # #  INSTANCE METHODS

    def __dir__(self) -> list[str]:
        return sorted(set(
            tuple(dir(type(self))) + tuple(self.__slots__) + tuple(self.keys()) + tuple(
                self._SCHEMA.get('properties', {}).keys())
        ))

    def __getattribute__(self, key: str) -> Any:
        """Get a defined attribute or dictionary key.

        :return: An object attribute if defined, else an internal key value, where key must be in schema.
        :raises KeyError: Key not defined in the schema properties.
        :raises TypeError: Key is not an instance of str.
        """
        if key in dir(type(self)):
            if key in super().__getattribute__('keys')() and not self._warned:
                warn(f'Key "{key}" of {self.__repr__()} is both a dictionary key and an object attribute. '
                     f'Make sure to call {type(self)}.get(key) to reliably get the key value.')
                SchemaHolder._warned = True
            return super().__getattribute__(key)

        return self.__getitem__(key)

    def __setattr__(self, key: str, value: Any) -> None:
        """Sets an object attribute if defined, else sets an internal key value, where key must be in schema.

        :raises KeyError: Key not defined in the schema properties.
        :raises TypeError: Key is not an instance of str.
        """
        if key in dir(type(self)):
            return super().__setattr__(key, value)

        self.__setitem__(key, value)

    def __delattr__(self, key: str) -> None:
        """Deletes an object attribute if defined, else pops an internal key value, where key must not be required.

        :raises KeyError: Key is either required or not defined in schema properties.
        :raises TypeError: Key is not an instance of str.
        """
        if key in dir(type(self)):
            return super().__delattr__(key)

        self.__delitem__(key)

    def __getitem__(self, key: str) -> Any:
        """Gets the value mapped to the given key.

        :raises KeyError: Key not defined in the schema properties.
        :raises TypeError: Key is not an instance of str.
        """
        if not isinstance(key, str):
            raise TypeError('Cannot lookup non-string values')

        value: Any

        if key in super().keys():
            value = super().__getitem__(key)
        else:
            if key not in self._SCHEMA.get('properties', ()):
                raise KeyError(f'Key "{key}" is not defined in the schema properties and is not an object attribute.')

            # Get default value from schema
            value = self._SCHEMA['properties'][key].get('default')

        props: dict = self._SCHEMA.get('properties', {}).get(key, NOT_FOUND)
        if props is not NOT_FOUND:
            value = self._conform_value(value, props)

        return value

    def __setitem__(self, key: str, value: Any) -> None:
        """Maps the given value to the given key.

        :raises KeyError: Key not defined in the schema properties.
        :raises TypeError: Key is not an instance of str.
        """
        if not isinstance(key, str):
            raise TypeError(f'Cannot set non-string key "{key}".')

        if key not in self._SCHEMA.get('properties', {}):
            raise KeyError(f'Key "{key}" is not defined in the schema properties and cannot be set.')

        props: dict = self._SCHEMA.get('properties', {}).get(key, NOT_FOUND)
        if props is not NOT_FOUND:
            value = self._conform_value(value, props)

        super().__setitem__(key, value)

    def __delitem__(self, key: str) -> None:
        """Deletes a key-value pair.

        :raises KeyError: Key not defined in the schema properties.
        :raises TypeError: Key is not an instance of str.
        """
        if not isinstance(key, str):
            raise TypeError(f'Cannot delete non-string key "{key}".')

        if key in self._SCHEMA.get('required', ()):
            raise KeyError(f'You cannot delete required key "{key}".')

        super().__delitem__(key)

    def __repr__(self) -> str:
        return f'<SchemaHolder dict {self}>'

    def __str__(self) -> str:
        return dict.__repr__(self)

    def _cache_ref_schema(self, ref_path: str) -> None:
        """Create a new schema holder using the definition found from the ref_path, then cache it."""
        schema_class: type
        definition: dict[str, Any] = self._SCHEMA

        for obj in ref_path.split('/')[1:]:
            definition = definition[obj]
        if definition.get('$ref', '').replace('/', '') == '#':
            definition = self._SCHEMA

        # Create a new schema holder using the definition found from the $ref value
        class CachedSchema(SchemaHolder):
            """Dynamically generated schema class meant to be cached for later use."""
            _SCHEMA = definition

            @classmethod
            def empty(cls) -> 'CachedSchema': return cls()

        schema_class = CachedSchema
        self.__REF_CACHE[ref_path] = schema_class

    def _conform_value(self, value: dict[str, Any], props: dict[str, Any]) -> 'SchemaHolder':
        """Automatically translate JSON objects and arrays with a $ref schema to SchemaHolders"""
        ref_type: int = 1 if ('$ref' in props) else 2 if ('$ref' in props.get('items', ())) else 0
        if ref_type and not isinstance(value, SchemaHolder):
            ref_path: str = props['$ref'] if (ref_type == 1) else (props['items']['$ref'] if (ref_type == 2) else None)
            schema_class: type

            if ref_path.replace('/', '') == '#':
                schema_class = self.__class__
            if ref_path not in self.__REF_CACHE:
                self._cache_ref_schema(ref_path)

            # Get cached class for reference
            schema_class = locals().get('schema_class') or self.__REF_CACHE[ref_path]

            value = schema_class(value) if ref_type == 1 else [schema_class(item) for item in value] if ref_type == 2 else None
        return value

    def default_of(self, key: str) -> Any:
        """Get the default value of a JSON schema's key.

        :return: The default in the key's properties, if the properties exist. Otherwise, dyncommands.schemas.constants.NOT_FOUND.
        :raise KeyError: properties must be defined as a top-level key in the _SCHEMA.
        """
        properties: dict[str, dict[str, Any]] = self._SCHEMA['properties']
        value = properties.get(key, NOT_FOUND)
        if value is not NOT_FOUND:
            value = value.get('default')
        return value

    def get(self, key: str, default: Any = None) -> Any:
        """Extends dict.get to allow use of schema default values.

        :param key: key to get value from; must be a str.
        :param default: set to dyncommands.schemas.constants.SCHEMA_DEFAULT to get the schema's default value if not found.
        """
        if default is SCHEMA_DEFAULT:
            default = self.default_of(key)

        return super().get(key, default)


class CommandData(SchemaHolder):
    """Python mapping to command.schema.json objects."""
    __slots__ = ()
    _SCHEMA: Final[dict[str, Any]] = get_schema('command')
    _validator: Final[Draft7Validator] = Draft7Validator(_SCHEMA)

    @classmethod
    def empty(cls) -> 'CommandData':
        return cls(name='')

    def __init__(self, seq=None, **kwargs) -> None:
        seq = seq if seq is not None else {}
        kw = [
            kwargs.pop('name', NOT_FOUND),
            kwargs.pop('description', NOT_FOUND),
            kwargs.pop('usage', NOT_FOUND),
            kwargs.pop('permission', NOT_FOUND),
            kwargs.pop('function', NOT_FOUND),
            kwargs.pop('children', NOT_FOUND),
            kwargs.pop('overridable', NOT_FOUND),
            kwargs.pop('disabled', NOT_FOUND),
        ]

        super().__init__(seq, **kwargs)
        self.name = kw[0] if kw[0] is not NOT_FOUND else seq['name']
        if kw[1] is not NOT_FOUND: self.description: str = kw[1]
        if kw[2] is not NOT_FOUND: self.usage: str = kw[2]
        if kw[3] is not NOT_FOUND: self.permission: int = kw[3]
        if kw[4] is not NOT_FOUND: self.function: Optional[bool] = kw[4]
        if kw[5] is not NOT_FOUND or self.get('children') is not None:
            self.children = kw[5] if kw[5] is not NOT_FOUND else [CommandData(child) for child in self.get('children', ())]
        if kw[6] is not NOT_FOUND: self.overridable = kw[6]
        if kw[7] is not NOT_FOUND: self.disabled = kw[7]


class ParserData(SchemaHolder):
    """Python mapping to parser.schema.json objects."""
    __slots__ = ()
    _SCHEMA: Final[dict[str, Any]] = SCHEMA
    _validator: Final[Draft7Validator] = Draft7Validator(_SCHEMA)

    @classmethod
    def empty(cls) -> 'ParserData':
        return cls(commandPrefix='', commands=[])

    def __init__(self, seq=None, **kwargs) -> None:
        seq = seq if seq is not None else {}
        kw = [
            kwargs.pop('commandPrefix', NOT_FOUND),
            kwargs.pop('commands', NOT_FOUND),
        ]

        super().__init__(seq, **kwargs)
        self.commandPrefix = kw[0] if kw[0] is not NOT_FOUND else seq['commandPrefix']
        self.commands = kw[1] if kw[1] is not NOT_FOUND else [CommandData(command) for command in self.get('commands', ())]
