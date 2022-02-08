###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Tests for the dyncommands.schemas module."""
import json
import sys
import unittest
from pathlib import Path

from jsonschema.exceptions import *

from dyncommands.schemas import *
from dyncommands.schemas.constants import SCHEMA_DEFAULT

# Boilerplate to allow running script directly.
if __name__ == '__main__' and __package__ is None: sys.path.insert(1, str(Path(__file__).resolve().parent.parent)); __package__ = 'tests'

with (Path(__file__).parent / 'data/schemas/test.schema.json').open('r', encoding='utf8') as _file:
    TEST_SCHEMA = json.load(_file)


class TestSchemaHolder(unittest.TestCase):
    class _Test(SchemaHolder):
        __slots__ = ()
        _SCHEMA = TEST_SCHEMA

        def __init__(self, seq=None, **kwargs) -> None:
            seq = seq if seq is not None else {}
            kw = [
                kwargs.pop('required', None),
                kwargs.pop('normal', None),
                kwargs.pop('get', None),
            ]

            super().__init__(seq if seq is not None else {}, **kwargs)
            self.required = kw[0] if kw[0] is not None else seq['required']
            if kw[1] is not None: self.normal = kw[1]
            if kw[2] is not None: self.get = kw[2]

        @classmethod
        def empty(cls) -> 'TestSchemaHolder._Test':
            return cls(required='')

    def setUp(self) -> None:
        self.test_holder = self._Test({'required': '', 'normal': '', 'get': 'test get'})
        self._Test.validate(self.test_holder)

    def test_NotImplemented(self) -> None:
        """All required attributes must be implemented"""
        with self.assertRaises(NotImplementedError):
            class _test0_(SchemaHolder):
                ...

        with self.assertRaises(NotImplementedError):
            class _test1_(SchemaHolder):
                _SCHEMA = TEST_SCHEMA

            _test1_.empty()

    def test_dir(self) -> None:
        """SchemaHolder.__dir__"""
        expected = sorted(set(dir(type(self.test_holder)) + list(self.test_holder._SCHEMA.get('properties', {}).keys())))
        result = dir(self.test_holder)

        self.assertEqual(expected, result)

    def test_getattribute(self) -> None:
        """Getting attribute values"""
        with self.assertRaises(KeyError):
            _ = self.test_holder.non_existent

        # Get an inherited method
        self.assertEqual(type(self.test_holder.pop), type({}.pop))
        self.assertIsNone(self.test_holder.get('pop'))

    def test_setattr(self) -> None:
        """Setting attribute values"""
        with self.assertRaises(KeyError):
            self.test_holder.non_existent = 1

        # Inherited attributes are read-only
        with self.assertRaises(AttributeError):
            self.test_holder._SCHEMA = {}

        self.test_holder.normal = 'wow'
        self.assertEqual('wow', self.test_holder.normal)

        self.assertIsNone(self.test_holder.get('_SCHEMA'))

    def test_delattr(self) -> None:
        """Deleting attributes"""
        with self.assertRaises(KeyError):
            del self.test_holder.non_existent

        # Inherited attributes are read-only
        with self.assertRaises(AttributeError):
            del self.test_holder._SCHEMA

        # Delete a required key
        with self.assertRaises(KeyError):
            del self.test_holder.required

        # Delete a normal key
        del self.test_holder.normal

    # noinspection PyTypeChecker
    def test_item_lookups(self) -> None:
        """Non-existent keys not working with SchemaHolder.__getitem__"""
        with self.assertRaises(TypeError):
            _ = self.test_holder[None]

        with self.assertRaises(TypeError):
            self.test_holder[None] = None

        with self.assertRaises(TypeError):
            del self.test_holder[None]

    def test_get(self) -> None:
        """SchemaHolder.get method working with the SCHEMA_DEFAULT constant"""
        self.assertEqual('', self.test_holder.get('normal'))
        self.assertEqual('', self.test_holder.get('normal', SCHEMA_DEFAULT))
        del self.test_holder['normal']

        self.assertEqual(None, self.test_holder.get('normal'))
        self.assertEqual('test default value', self.test_holder.get('normal', SCHEMA_DEFAULT))
        self.assertEqual(self.test_holder.default_of('normal'), self.test_holder.get('normal', SCHEMA_DEFAULT))

        self.assertIsNot(self.test_holder.get, self.test_holder.get('get'))
        self.assertEqual('test get', self.test_holder.get('get'))


class TestCommandData(unittest.TestCase):
    def setUp(self) -> None:
        self.test_command = CommandData.empty()

    def test_commands_json(self) -> None:
        """All command objects in commands.json file are valid CommandData"""
        with (Path(__file__).parent / 'data/commands/commands.json').open(mode='r', encoding='utf8') as file:
            for command in json.loads(file.read())['commands']:
                CommandData.validate(command)

    def test_defaults(self) -> None:
        """Default values of CommandData"""
        self.assertRaises(KeyError, CommandData)
        self.assertRaises(KeyError, CommandData, {})
        self.assertEqual(self.test_command.name, '')
        self.assertEqual(self.test_command.description, '')
        self.assertEqual(self.test_command.usage, '')
        self.assertEqual(self.test_command.permission, 0)
        self.assertFalse(self.test_command.function)
        self.assertListEqual(self.test_command.children, [])
        self.assertTrue(self.test_command.overridable)
        self.assertFalse(self.test_command.disabled)

    def test_validate(self) -> None:
        """CommandData.validate blocking invalid json data"""
        CommandData.validate(self.test_command)
        self.assertRaises(ValidationError, CommandData.validate, {})
        self.assertRaises(ValidationError, CommandData.validate, {'name': 0})
        self.assertRaises(ValidationError, CommandData.validate, {'name': '', 'description': 0})
        self.assertRaises(ValidationError, CommandData.validate, {'name': '', 'usage': 0})
        self.assertRaises(ValidationError, CommandData.validate, {'name': '', 'permission': None})
        self.assertRaises(ValidationError, CommandData.validate, {'name': '', 'function': ''})
        self.assertRaises(ValidationError, CommandData.validate, {'name': '', 'overridable': None})
        self.assertRaises(ValidationError, CommandData.validate, {'name': '', 'disabled': None})


class TestParserData(unittest.TestCase):
    def setUp(self) -> None:
        self.test_data = ParserData.empty()

    def test_commands_json(self) -> None:
        """commands.json file in test data is valid ParserData"""
        with (Path(__file__).parent / 'data/commands/commands.json').open(mode='r', encoding='utf8') as file:
            ParserData.validate(json.loads(file.read()))

    def test_defaults(self) -> None:
        """Default values of ParserData"""
        self.assertRaises(KeyError, ParserData)
        self.assertRaises(KeyError, ParserData, {})
        self.assertEqual(self.test_data.commandPrefix, '')
        self.assertListEqual(self.test_data.commands, [])

    def test_validate(self) -> None:
        """ParserData.validate blocking invalid json data"""
        ParserData.validate(self.test_data)
        self.assertRaises(ValidationError, ParserData.validate, {})
        self.assertRaises(ValidationError, ParserData.validate, {'commands': []})
        self.assertRaises(ValidationError, ParserData.validate, {'commandPrefix': None})
        self.assertRaises(ValidationError, ParserData.validate, {'commandPrefix': None, 'commands': []})
        self.assertRaises(ValidationError, ParserData.validate, {'commandPrefix': '', 'commands': None})
        self.assertRaises(ValidationError, ParserData.validate, {'commandPrefix': '', 'commands': [0, 1, 2, 3]})


if __name__ == '__main__':
    unittest.main()
