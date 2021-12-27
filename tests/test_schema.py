###################################################################################################
#                              MIT Licence (C) 2021 Cubicpath@Github                              #
###################################################################################################
"""Tests for the schema.py module."""
import json
import sys
import unittest
from pathlib import Path

from jsonschema.exceptions import *

from dyncommands.schema import *

# Boilerplate to allow running script directly.
if __name__ == '__main__' and __package__ is None: sys.path.insert(1, str(Path(__file__).resolve().parent.parent)); __package__ = 'tests'


class TestCommandData(unittest.TestCase):
    def setUp(self) -> None:
        self.test_command = CommandData(name='')

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

    def test_slots(self) -> None:
        with self.assertRaises(AttributeError):
            self.test_command.non_existent = 1

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
        self.test_data = ParserData({'commandPrefix': '', 'commands': []})

    def test_commands_json(self) -> None:
        with (Path(__file__).parent / 'data/commands/commands.json').open(mode='r', encoding='utf8') as file:
            ParserData.validate(json.loads(file.read()))

    def test_defaults(self) -> None:
        self.assertRaises(KeyError, ParserData)
        self.assertRaises(KeyError, ParserData, {})
        self.assertEqual(self.test_data.command_prefix, '')
        self.assertListEqual(self.test_data.commands, [])

    def test_slots(self) -> None:
        with self.assertRaises(AttributeError):
            self.test_data.non_existent = 1

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
