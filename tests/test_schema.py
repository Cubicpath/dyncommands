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

SchemaCommand = CommandData.SchemaCommand

# Boilerplate to allow running script directly.
if __name__ == '__main__' and __package__ is None: sys.path.insert(1, str(Path(__file__).resolve().parent.parent)); __package__ = 'tests'


class TestSchemaCommand(unittest.TestCase):
    def setUp(self) -> None:
        self.test_command = SchemaCommand({'name': ''})

    def test_commands_json(self):
        with (Path(__file__).parent / 'data/commands/commands.json').open(mode='r', encoding='utf8') as file:
            for command in json.loads(file.read())['commands']:
                SchemaCommand.validate(command)

    def test_defaults(self):
        self.assertRaises(TypeError, SchemaCommand)
        self.assertRaises(KeyError, SchemaCommand, {})
        self.assertEqual(self.test_command.name, '')
        self.assertEqual(self.test_command.description, '')
        self.assertEqual(self.test_command.usage, '')
        self.assertEqual(self.test_command.permission, 0)
        self.assertFalse(self.test_command.function)
        self.assertListEqual(self.test_command.children, [])
        self.assertTrue(self.test_command.overridable)
        self.assertFalse(self.test_command.disabled)

    def test_slots(self):
        with self.assertRaises(AttributeError):
            self.test_command.non_existent = 1

    def test_validate(self):
        SchemaCommand.validate(self.test_command)
        self.assertRaises(ValidationError, SchemaCommand.validate, {})
        self.assertRaises(ValidationError, SchemaCommand.validate, {'name': 0})
        self.assertRaises(ValidationError, SchemaCommand.validate, {'name': '', 'description': 0})
        self.assertRaises(ValidationError, SchemaCommand.validate, {'name': '', 'usage': 0})
        self.assertRaises(ValidationError, SchemaCommand.validate, {'name': '', 'permission': None})
        self.assertRaises(ValidationError, SchemaCommand.validate, {'name': '', 'function': ''})
        self.assertRaises(ValidationError, SchemaCommand.validate, {'name': '', 'overridable': None})
        self.assertRaises(ValidationError, SchemaCommand.validate, {'name': '', 'disabled': None})


class TestCommandData(unittest.TestCase):
    def setUp(self) -> None:
        self.test_data = CommandData({'commandPrefix': '', 'commands': []})

    def test_commands_json(self):
        with (Path(__file__).parent / 'data/commands/commands.json').open(mode='r', encoding='utf8') as file:
            CommandData.validate(json.loads(file.read()))

    def test_defaults(self):
        self.assertRaises(TypeError, CommandData)
        self.assertRaises(ValidationError, CommandData, {})
        self.assertEqual(self.test_data.commandPrefix, '')
        self.assertListEqual(self.test_data.commands, [])

    def test_slots(self):
        with self.assertRaises(AttributeError):
            self.test_data.non_existent = 1

    def test_validate(self):
        CommandData.validate(self.test_data)
        self.assertRaises(ValidationError, CommandData.validate, {})
        self.assertRaises(ValidationError, CommandData.validate, {'commands': []})
        self.assertRaises(ValidationError, CommandData.validate, {'commandPrefix': None})
        self.assertRaises(ValidationError, CommandData.validate, {'commandPrefix': None, 'commands': []})
        self.assertRaises(ValidationError, CommandData.validate, {'commandPrefix': '', 'commands': None})
        self.assertRaises(ValidationError, CommandData.validate, {'commandPrefix': '', 'commands': [0, 1, 2, 3]})


if __name__ == '__main__':
    unittest.main()
