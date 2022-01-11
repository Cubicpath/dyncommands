###################################################################################################
#                              MIT Licence (C) 2021 Cubicpath@Github                              #
###################################################################################################
"""Tests for the parser.py and exceptions.py modules."""
import io
import random
import string
import sys
import unittest
from pathlib import Path
from shutil import copytree
from shutil import rmtree

from dyncommands import *
from dyncommands.exceptions import *
from dyncommands.schemas import CommandData
from dyncommands.utils import get_raw_text

# Boilerplate to allow running script directly.
if __name__ == '__main__' and __package__ is None: sys.path.insert(1, str(Path(__file__).resolve().parent.parent)); __package__ = 'tests'

temp_path = Path(__file__).parent / 'data/temp/commands'


def make_parser_env():
    rmtree(temp_path, ignore_errors=True)
    copytree(temp_path.parent.parent / 'commands', temp_path)


class TestExceptions(unittest.TestCase):
    """Tests for the exceptions module"""
    parser: CommandParser

    @classmethod
    def setUpClass(cls) -> None:
        make_parser_env()
        cls.parser = CommandParser(temp_path, silent=True)

    @classmethod
    def tearDownClass(cls) -> None:
        rmtree(temp_path)

    def setUp(self) -> None:
        self.test_context = CommandContext('!w')
        self.test_command = Command(CommandData(name='w'), self.parser)

    def test_CommandError(self) -> None:
        """General failure of command execution"""
        e = CommandError(self.test_command, self.test_context)
        self.error_assert(e)
        self.assertEqual(f"'{e.context.source.display_name}' failed executing the '{e.command.name}' command.", str(e))
        self.test_context = CommandContext('!commands a', self.test_context.source)

    def test_DisabledError(self) -> None:
        """Improperly use commands"""
        e = DisabledError(self.test_command, self.test_context)
        self.error_assert(e)
        self.parser.set_disabled('test', True)
        self.assertEqual(f"'{e.command.name}' is disabled, enable to execute.", str(e))
        self.test_context = CommandContext('!test', self.test_context.source)
        self.assertRaises(DisabledError, self.parser.parse, self.test_context)
        self.parser.set_disabled('test', False)

    def test_ImproperUsageError(self) -> None:
        """Improperly use commands"""
        e = ImproperUsageError(self.test_command, self.test_context)
        self.error_assert(e)
        self.assertEqual(f"Incorrect usage of '{e.command.name}'. To view usage information, use '!#prefix#!help {e.command.name}'.", str(e))
        self.test_context = CommandContext('!commands a b', self.test_context.source)
        self.assertRaises(ImproperUsageError, self.parser.parse, self.test_context)

    def test_NoPermissionError(self) -> None:
        """Executing command without required permissions"""
        e = NoPermissionError(self.test_command, self.test_context)
        self.error_assert(e)
        self.assertEqual(f"'{e.context.source.display_name}' did not have the required permissions ({e.context.source.permission}/{e.command.permission}) to use the '{e.command.name}' command.", str(e))
        self.test_context = CommandContext('!test', self.test_context.source)
        self.assertRaises(NoPermissionError, self.parser.parse, self.test_context)

    def test_NotFoundError(self) -> None:
        """Non-existent command name"""
        e = NotFoundError(self.test_command.name, self.test_context)
        self.error_assert(e)
        self.assertEqual(f"'w' is not a registered command.", str(e))
        self.assertRaises(NotFoundError, self.parser.parse, self.test_context)

    def error_assert(self, e: CommandError) -> None:
        self.assertIsInstance(e, (type(e), CommandError))
        if type(e) is CommandError: self.assertIsNone(e.parent)
        else: self.assertIs(e, e.parent)
        self.assertIs(self.test_context, e.context)
        self.assertIs(self.test_command, e.command or self.test_command)


class TestCommandParser(unittest.TestCase):
    """Tests for the parser module"""
    parser: CommandParser

    @classmethod
    def setUpClass(cls) -> None:
        make_parser_env()
        cls.old_stdout = sys.stdout  # Memorize the default stdout
        cls.parser = parser = CommandParser(temp_path, silent=True)
        cls.original_prefix = parser.prefix

    @classmethod
    def tearDownClass(cls) -> None:
        rmtree(temp_path)

    def setUp(self) -> None:
        self.test_source = CommandSource(self.feedback_receiver)
        self.feedback = ''
        self.buffer = sys.stdout = io.StringIO()

    def tearDown(self) -> None:
        sys.stdout = self.old_stdout
        self.parser.prefix = self.original_prefix

    def test_add_command(self) -> None:
        broken_command_link = 'https://gist.github.com/Cubicpath/8fc611ca67bf2d17e03b4766a816596a'
        with (self.parser.path / 'zzz__commands.py').open(mode='r', encoding='utf8') as file:
            command0 = file.read()
        with (self.parser.path / 'zzz__test.py').open(mode='r', encoding='utf8') as file:
            command1 = file.read()
        with (self.parser.path / 'test-no-command.txt').open(mode='r', encoding='utf8') as file:
            command2 = file.read()
        with (self.parser.path / 'test-docstring.txt').open(mode='r', encoding='utf8') as file:
            command3 = file.read()
        with (self.parser.path / 'test-metadata-error.txt').open(mode='r', encoding='utf8') as file:
            command4 = file.read()
        self.assertEqual(self.parser.add_command(text=command0), '')
        self.assertEqual(self.parser.add_command(text=command1), 'test')
        self.assertEqual(self.parser.add_command(text=broken_command_link, link=True), 'broken')
        self.assertEqual(self.parser.add_command(text=command2), '')
        self.assertEqual(self.parser.add_command(text=command3), 'test-docstring')
        self.assertEqual(self.parser.add_command(text=command4), 'test-metadata-error')
        self.parser.reload()
        self.assertEqual(self.parser.commands['test'].name, 'test')
        self.assertEqual(self.parser.commands['test'].usage, 'test [*args:Any]')
        self.assertEqual(self.parser.commands['test'].description, 'Test command.')
        self.assertEqual(self.parser.commands['test'].permission, 500)
        self.assertEqual(self.parser.commands['test'].children, {})
        self.assertEqual(self.parser.commands['test-metadata-error'].permission, 0)
        self.assertIsNone(self.parser.commands.get('broken'))
        self.assertRaises(FileNotFoundError, CommandParser, 'bad_path')

    def test_parse(self) -> None:
        """Command parsing"""
        for substring_tup in [(char,) for char in string.printable.rstrip(string.whitespace)] + [('!#',)] + [('(5352)',)]:
            self.assert_prefix(substring_tup[0])
        self.test_source.permission = 1000
        context = CommandContext('test', self.test_source)
        self.parser(context)
        self.parser.parse(context)
        self.assertEqual(self.feedback, f"'{context.working_string.strip()}' is correct usage of the 'test' command.")

    def test_remove_command(self) -> None:
        # Test overridable as false
        self.assertEqual(self.parser.remove_command('commands'), '')
        self.assertIn('commands', self.parser.commands)

        # Remove non-existent command
        self.assertEqual(self.parser.remove_command('mc983jn784'), '')
        self.assertNotIn('mc983jn784', self.parser.commands)

        # Test function as false
        self.assertEqual(self.parser.remove_command('test-no-function'), 'test-no-function')
        self.assertNotIn('test-no-function', self.parser.commands)

    def test_set_disabled(self) -> None:
        self.assertFalse(self.parser.set_disabled('commands', True))
        self.assertTrue(self.parser.set_disabled('test', True))
        self.assertFalse(self.parser.commands['commands'].disabled)
        self.assertTrue(self.parser.commands['test'].disabled)
        self.parser.set_disabled('test', False)

    def test_silent(self) -> None:
        # Buffer shouldn't change
        self.assertTrue(self.parser._silent)
        old_output = self.buffer.getvalue()
        self.parser.print('test')
        self.assertEqual(old_output, self.buffer.getvalue())

        # Buffer should change
        self.parser._silent = False
        self.assertFalse(self.parser._silent)
        old_output = self.buffer.getvalue()
        self.parser.print('test')
        self.assertNotEqual(old_output, self.buffer.getvalue())

    def assert_prefix(self, prefix: str) -> None:
        self.parser.prefix = prefix
        context = CommandContext(self.parser.prefix + ''.join(random.choices(string.printable.rstrip(string.whitespace) + ' ', k=random.randint(20, 40))), self.test_source)
        self.assertEqual(self.parser.prefix, prefix)
        self.assertRaises(NotFoundError, self.parser.parse, context)

    def feedback_receiver(self, s: str, *_) -> None:
        self.feedback = s


class TestUnrestricted(unittest.TestCase):
    parser: CommandParser

    @classmethod
    def setUpClass(cls) -> None:
        make_parser_env()
        cls.parser = CommandParser(temp_path, silent=True, unrestricted=True)

    @classmethod
    def tearDownClass(cls) -> None:
        rmtree(temp_path)

    def setUp(self) -> None:
        self.test_source = CommandSource(self.feedback_receiver)
        self.feedback = ''

    def test_should_hide_attr(self):
        self.assertFalse(self.parser._should_hide_attr('_protected_attribute', object()))
        self.assertFalse(self.parser._should_hide_attr('path_object', temp_path))

    def test_parse(self):
        context = CommandContext('unrestricted arg1 arg2', self.test_source)
        self.parser.parse(context)
        self.assertEqual(self.feedback, get_raw_text('https://gist.github.com/Cubicpath/8fc611ca67bf2d17e03b4766a816596a'))

    def feedback_receiver(self, s: str, *_) -> None:
        self.feedback = s


if __name__ == '__main__':
    unittest.main()
