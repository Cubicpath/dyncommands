###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Tests for the schema.py module."""
import json
import sys
import unittest
from pathlib import Path

from jsonschema.exceptions import *

from dyncommands.schemas import *

# Boilerplate to allow running script directly.
if __name__ == '__main__' and __package__ is None: sys.path.insert(1, str(Path(__file__).resolve().parent.parent)); __package__ = 'tests'

with (Path(__file__).parent / 'data/schemas/test.schema.json').open('r', encoding='utf8') as _file:
    TEST_SCHEMA = json.load(_file)


class TestSchemaHolder(unittest.TestCase):
    class _Test(SchemaHolder):
        __slots__ = ()
        _SCHEMA = TEST_SCHEMA

        def __init__(self, seq=None, **kwargs) -> None:
            kw = [
                kwargs.pop('required', None),
            ]

            super().__init__(seq if seq is not None else {}, **kwargs)
            self.required = kw[0] if kw[0] is not None else self['required']

        @classmethod
        def empty(cls) -> 'TestSchemaHolder._Test':
            return cls(required='')

    def setUp(self) -> None:
        self.test_holder = self._Test.empty()

    def test_NotImplemented(self) -> None:
        with self.assertRaises(NotImplementedError):
            class _test_(SchemaHolder):
                ...

    def test_getattr(self) -> None:
        _ = getattr(self.test_holder, 'pop')
        with self.assertRaises(KeyError):
            _ = self.test_holder.non_existent

        # Get an inherited method
        self.assertEqual(type(self.test_holder.pop), type({}.pop))
        self.assertIsNone(self.test_holder.get('pop'))

    def test_setattr(self) -> None:
        with self.assertRaises(KeyError):
            self.test_holder.non_existent = 1

        # Inherited methods are read-only
        with self.assertRaises(AttributeError):
            self.test_holder._SCHEMA = {}

        self.assertIsNone(self.test_holder.get('_SCHEMA'))

    def test_delattr(self) -> None:
        with self.assertRaises(KeyError):
            del self.test_holder.non_existent

        # Inherited methods are read-only
        with self.assertRaises(AttributeError):
            del self.test_holder._SCHEMA

        # Delete a required key
        with self.assertRaises(KeyError):
            del self.test_holder.required


class TestCommandData(unittest.TestCase):
    def setUp(self) -> None:
        self.test_command = CommandData.empty()

    def test_commands_json(self) -> None:
        with (Path(__file__).parent / 'data/commands/commands.json').open(mode='r', encoding='utf8') as file:
            for command in json.loads(file.read())['commands']:
                CommandData.validate(command)

    def test_defaults(self) -> None:
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
        with (Path(__file__).parent / 'data/commands/commands.json').open(mode='r', encoding='utf8') as file:
            ParserData.validate(json.loads(file.read()))

    def test_defaults(self) -> None:
        self.assertRaises(KeyError, ParserData)
        self.assertRaises(KeyError, ParserData, {})
        self.assertEqual(self.test_data.commandPrefix, '')
        self.assertListEqual(self.test_data.commands, [])

    def test_validate(self) -> None:
        ParserData.validate(self.test_data)
        self.assertRaises(ValidationError, ParserData.validate, {})
        self.assertRaises(ValidationError, ParserData.validate, {'commands': []})
        self.assertRaises(ValidationError, ParserData.validate, {'commandPrefix': None})
        self.assertRaises(ValidationError, ParserData.validate, {'commandPrefix': None, 'commands': []})
        self.assertRaises(ValidationError, ParserData.validate, {'commandPrefix': '', 'commands': None})
        self.assertRaises(ValidationError, ParserData.validate, {'commandPrefix': '', 'commands': [0, 1, 2, 3]})


if __name__ == '__main__':
    unittest.main()
