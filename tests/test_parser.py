###################################################################################################
#                              MIT Licence (C) 2021 Cubicpath@Github                              #
###################################################################################################
"""Tests for the parser.py and exceptions.py modules."""
# Boilerplate to allow running script directly.
if __name__ == "__main__" and __package__ is None: import sys, os; sys.path.insert(1, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); __package__ = 'tests'; del sys, os

import os
import random
import string
import unittest

from dyncommands import *

parser = CommandParser(commands_path=f'{os.path.dirname(__file__)}/data/commands', silent=True)
orig_prefix = parser.prefix


class TestExceptions(unittest.TestCase):
    """Tests for the exceptions module"""

    def setUp(self) -> None:
        self.test_context = CommandContext('!w')
        self.test_command = Command('w', parser)

    def test_CommandError(self):
        """General failure of command execution"""
        e = CommandError(self.test_command, self.test_context)
        self.error_assert(e)
        self.assertEqual(f"'{e.context.source.display_name}' failed executing the '{e.command.name}' command.", str(e))
        self.test_context = CommandContext('!commands a', self.test_context.source)

    def test_DisabledError(self):
        """Improperly use commands"""
        e = DisabledError(self.test_command, self.test_context)
        self.error_assert(e)
        parser.set_disabled('test', True)
        self.assertEqual(f"'{e.command.name}' is disabled, enable to execute.", str(e))
        self.test_context = CommandContext('!test', self.test_context.source)
        self.assertRaises(DisabledError, parser.parse, self.test_context)
        parser.set_disabled('test', False)

    def test_ImproperUsageError(self):
        """Improperly use commands"""
        e = ImproperUsageError(self.test_command, self.test_context)
        self.error_assert(e)
        self.assertEqual(f"Incorrect usage of '{e.command.name}'. To view usage information, use '!#prefix#!help {e.command.name}'.", str(e))
        self.test_context = CommandContext('!commands a b', self.test_context.source)
        self.assertRaises(ImproperUsageError, parser.parse, self.test_context)

    def test_NoPermissionError(self):
        """Executing command without required permissions"""
        e = NoPermissionError(self.test_command, self.test_context)
        self.error_assert(e)
        self.assertEqual(f"'{e.context.source.display_name}' did not have the required permissions ({e.context.source.permission}/{e.command.permission}) to use the '{e.command.name}' command.", str(e))
        self.test_context = CommandContext('!test', self.test_context.source)
        self.assertRaises(NoPermissionError, parser.parse, self.test_context)

    def test_NotFoundError(self):
        """Non-existent command name"""
        e = NotFoundError(self.test_command, self.test_context)
        self.error_assert(e)
        self.assertEqual(f"'{e.command.name}' is not a registered command.", str(e))
        self.assertRaises(NotFoundError, parser.parse, self.test_context)

    def error_assert(self, e: CommandError):
        self.assertIsInstance(e, (type(e), CommandError))
        if type(e) is CommandError: self.assertIsNone(e.parent)
        else: self.assertIs(e, e.parent)
        self.assertIs(self.test_context, e.context)
        self.assertIs(self.test_command, e.command)


class TestCommandParser(unittest.TestCase):
    """Tests for the parser module"""

    def setUp(self) -> None:
        self.test_source = CommandSource(self.feedback_receiver)
        self.feedback = ''

    def tearDown(self) -> None:
        parser.prefix = orig_prefix

    def test_set_disabled(self):
        self.assertFalse(parser.set_disabled('commands', True))
        self.assertTrue(parser.set_disabled('test', True))
        self.assertFalse(parser.commands['commands'].disabled)
        self.assertTrue(parser.commands['test'].disabled)
        parser.set_disabled('test', False)

    def test_command_updating(self):
        broken_command_link = 'https://gist.github.com/Cubicpath/8fc611ca67bf2d17e03b4766a816596a'
        with open(parser.commands_path + '/zzz__test.py', encoding='utf8') as file:
            test_command = file.read()
        self.assertEqual(parser.add_command(text=test_command), 'test')
        self.assertEqual(parser.add_command(text=broken_command_link, link=True), 'broken')
        parser.reload()
        self.assertEqual(parser.commands['test'].name, 'test')
        self.assertEqual(parser.commands['test'].usage, 'test [*args:Any]')
        self.assertEqual(parser.commands['test'].description, 'Test command.')
        self.assertEqual(parser.commands['test'].permission, 500)
        self.assertEqual(parser.commands['test'].children, {})
        self.assertIsNone(parser.commands.get('broken'))

    def test_parse(self):
        """Command parsing"""
        for substring_tup in [(char,) for char in string.printable.rstrip(string.whitespace)] + [('!#',)] + [('(5352)',)]:
            self.assert_prefix(substring_tup[0])
        self.test_source.permission = 1000
        context = CommandContext('test', self.test_source)
        parser(context)
        parser.parse(context)
        self.assertEqual(self.feedback, f"'{context.working_string.strip()}' is correct usage of the 'test' command.")

    def assert_prefix(self, prefix: str):
        parser.prefix = prefix
        context = CommandContext(parser.prefix + ''.join(random.choices(string.printable.rstrip(string.whitespace) + ' ', k=random.randint(20, 40))), self.test_source)
        self.assertEqual(parser.prefix, prefix)
        self.assertRaises(NotFoundError, parser.parse, context)

    def feedback_receiver(self, s: str, *_) -> None:
        self.feedback = s


if __name__ == '__main__':
    unittest.main()
