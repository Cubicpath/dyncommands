###################################################################################################
#                              MIT Licence (C) 2021 Cubicpath@Github                              #
###################################################################################################
"""Parser for Dynamic Commands."""
import json
import operator
import os
from typing import Any
from typing import Optional

from RestrictedPython import compile_restricted as safe_compile
from RestrictedPython import limited_builtins
from RestrictedPython import RestrictingNodeTransformer
from RestrictedPython import safe_builtins
from RestrictedPython import utility_builtins
from RestrictedPython.Eval import default_guarded_getitem
from RestrictedPython.Eval import default_guarded_getiter
from RestrictedPython.Guards import guarded_iter_unpack_sequence
from RestrictedPython.Guards import guarded_unpack_sequence
from RestrictedPython.Guards import safer_getattr

from .exceptions import *
from .models import *
from .utils import *

__all__ = (
    'Command',
    'CommandParser',
)

command_builtins = safe_builtins.copy()
command_builtins.update(limited_builtins)
command_builtins.update(utility_builtins)
command_globals = {
    '__builtins__': command_builtins,
    '_getattr_': safer_getattr,
    '_getitem_': default_guarded_getitem,
    '_getiter_': default_guarded_getiter,
    '_iter_unpack_sequence_': guarded_iter_unpack_sequence,
    '_unpack_sequence_': guarded_unpack_sequence,
    'ImproperUsageError': ImproperUsageError,
    'getitem': operator.getitem
}


class _CommandPolicy(RestrictingNodeTransformer):
    ...


class Command(Node):
    """Dynamic command object. Created on demand by a CommandParser."""
    __slots__ = ('_function',)

    def __init__(self, name: str, parser: 'CommandParser') -> None:
        """Build command from parser data and matching zzz__ modules."""
        super().__init__()
        self.name = name
        self._function = DUMMY_FUNC

        for command in parser.command_data:
            if command['name'] == self.name:
                self.usage = command.get('usage', self.usage)
                self.description = command.get('description', self.description)
                self.permission = command.get('permission', self.permission)
                self.children = CaseInsensitiveDict({props['name']: Node(parent=self, **props) for props in command.get('children', [])})
                self.disabled = command.get('disabled', self.disabled)

                if command.get('function', False) is True:  # True, False, and None
                    self._load_function(parser)

    def __call__(self, *args, **kwargs) -> Optional[str]:
        """Syntax sugar for self._execute."""
        return self._execute(*args, **kwargs)

    # pylint: disable=exec-used
    def _load_function(self, parser: 'CommandParser'):
        """Loads in python code from storage for future execution."""
        namespace = {}
        file_path: str = f'{parser.commands_path}/zzz__{self.name}.py'
        try:
            with open(file_path, encoding='utf8') as file:
                # Attempt to compile code and run function definition
                plaintext_code = file.read()
                byte_code = safe_compile(plaintext_code, file_path, 'exec', policy=_CommandPolicy)
                exec(byte_code, command_globals, namespace)
        except (FileNotFoundError, SyntaxError, NotImplementedError) as e:
            parser.print(str(e))
            parser.print(f"Discarding broken command '{self.name}' from {file_path}.")
            parser.remove_command(self.name)
        else:
            parser.print(f"Loading file {file_path} from disk into '{self.name}'.")
            self._function = namespace.get('command', DUMMY_FUNC)

    # noinspection PyProtectedMember
    def _execute(self, *args, **kwargs) -> Optional[str]:
        """Command (or last node)'s permission must be at least 0 and equal to or less than the source's permission level.

        Otherwise, it will not execute.
        """
        context: CommandContext = kwargs['context']
        parser: 'CommandParser' = kwargs['parser']
        source: CommandSource = context.source
        kwargs['self'] = self
        if not self.disabled:
            try:
                # Get permission level of last argument with properties, or the command itself if no args with properties
                final_node: Node = self
                for arg in args:
                    final_node = final_node.children.get(arg, final_node)

                if source.has_permission(final_node.permission) or parser._ignore_permission:
                    # Proxy public attributes of kwargs
                    kwargs = {kwarg: PrivateProxy(kwval, lambda attr: True in (string in attr for string in ('path',))) for kwarg, kwval in kwargs.items()}
                    return self._function(*args, **kwargs)
                raise NoPermissionError(final_node, context)
            except Exception as e:
                raise CommandError(self, context, e) from e
        else:
            raise DisabledError(self, context)


class CommandParser:
    """Keeps track of all commands and command metadata. Allows for dynamic execution of commands through string parsing."""

    def __init__(self, commands_path: str, silent: bool = False, ignore_permission: bool = False) -> None:
        """Create a new Parser and load all command data from the given path.
        :param silent: If true, stops all debug printing.
        :param ignore_permission: If true, permission level is not taken into account when executing a command.
        """
        self.commands:          CaseInsensitiveDict[Command] = CaseInsensitiveDict()
        self.command_data:      list[dict[str, Any]] = []
        self.commands_path:     str = commands_path
        self.delimiting_str:    str = ' '
        self._command_prefix:   str = '/'
        self._current_command:  Optional[Command] = None
        self._ignore_permission: bool = ignore_permission
        self._silent:           bool = silent

        self.reload()

    def __call__(self, context: CommandContext, **kwargs):
        """Syntax sugar for self.parse."""
        self.parse(context=context, **kwargs)

    @property
    def prefix(self) -> str: return self._command_prefix

    @prefix.setter
    def prefix(self, value) -> None:
        self._command_prefix = value
        with open(f'{self.commands_path}/commands.json', encoding='utf8') as file:
            new_json: dict[str, Any] = json.load(file)
            new_json['commandPrefix'] = self._command_prefix
        with open(f'{self.commands_path}/commands.json', 'w', encoding='utf8') as file:
            json.dump(new_json, file, indent=2)

    def reload(self) -> None:
        """Load all data from the commands.json file in the commands_path.
        For every command JSON object, a Command object is constructed and assigned with the same name.
        """
        with open(f'{self.commands_path}/commands.json', encoding='utf8') as file:
            json_data = json.load(file)

        self._command_prefix = json_data['commandPrefix']
        self.command_data = json_data['commands']
        self.commands = CaseInsensitiveDict({command['name']: Command(command['name'], self) for command in self.command_data})

        # Load json data a second time to check for any remnant commands in memory that weren't removed during failed compilation
        with open(f'{self.commands_path}/commands.json', encoding='utf8') as file:
            updated_json_data = json.load(file)
        if json_data != updated_json_data:
            self.command_data = updated_json_data['commands']
            self.commands = CaseInsensitiveDict({command['name']: Command(command['name'], self) for command in self.command_data})

    def parse(self, context: CommandContext, **kwargs) -> None:
        """Parse a CommandContext's working_string for commands and arguments, then execute them.

        It is EXTREMELY recommended wrapping this function in a try-except block.

        :param context: Command context for parsing.
        :param kwargs: kwargs you want to  Command being parsed to have access to during execution.
        :raises DisabledError: When command specified in the contextual working string is disabled.
        :raises ImproperUsageError: Manually triggered exception from the command itself.
        :raises NoPermissionError: When contextual source does not have the required permissions.
        :raises NotFoundError: When command specified in the contextual working string is not found in the command data.
        """

        input_ = context.working_string.removeprefix(self.prefix).rstrip('\U000e0000').strip()
        if input_:
            split = input_.split(self.delimiting_str)
            name, args = split[0], split[1:]
            if self.commands.get(name) is not None:
                kwargs.update({'parser': self, 'context': context})
                try:
                    # Call command function with args and kwargs
                    return_val = self.commands[name](*args, **kwargs)
                    if return_val is not None:
                        # Return Value, if any
                        context.source.send_feedback(str(return_val), context.source.display_name)
                except CommandError as e:
                    self.print(e.parent.__class__.__name__ + " while executing command: " + str(e.parent))
                    if isinstance(e.parent, ImproperUsageError):
                        # Negative feedback
                        message = str(e.parent)
                        if message:
                            context.source.send_feedback(message.replace('!#prefix#!', self.prefix), context.source.display_name)
                    if isinstance(e.parent, CommandError):
                        raise e.parent from e
            else:
                raise NotFoundError(Command(name, self), context)

    def print(self, *values: object, sep: Optional[str] = None, end: Optional[str] = None, file: Optional[object] = None, flush: bool = False) -> None:
        """Print if not self._silent."""
        if not self._silent: print(*values, sep=sep, end=end, file=file, flush=flush)

    def set_disabled(self, command_name: str, value: bool) -> bool:
        """
        Set a command as disabled.

        :param command_name: Command to disable.
        :param value: Whether disabled or not.
        :return: If disabled state successfully changed.
        """
        with open(f'{self.commands_path}/commands.json', encoding='utf8') as file:
            data: dict[str, Any] = json.load(file)
            commands: dict[str, dict] = {command['name']: command for command in data.get('commands')}

            if commands.get(command_name, {}).get('overridable') is not False:
                commands[command_name]['disabled'] = value
                self.commands.get(command_name).disabled = value
            else:
                return False

            data.update({'commands': list(commands.values())})

        with open(f'{self.commands_path}/commands.json', 'w', encoding='utf8') as file:
            json.dump(data, file, indent=2)

        return True

    def add_command(self, text: str, link: bool = False, **kwargs) -> str:
        """
        Adds a command using data read from {text}. Command metadata must either be passed in through a kwarg,
        or structured as an inline python comment above the command function. Ex:

        # Name: do-nothing
        # Usage: do-nothing [amount:integer sides:integer]
        # Description: Rolls die.
        # Permission: 0
        def command(*args, **kwargs):
            pass

        :param text: Body of text or a link to read command data from.
        :param link: Whether {text} is a link.
        :param kwargs: kwargs to override data read from text.
        :return: Name of command added if successful, else empty string.
        """
        def get_data(line_: str, name_: str) -> str:
            return ireplace(line_, name_, '', 1).split(':', 1)[1].strip()

        text = get_raw_text(text) if link else text
        lines = text.splitlines(True)
        command_data:    list[Any] = [
            kwargs.pop('name', ''),
            kwargs.pop('usage', ''),
            kwargs.pop('description', ''),
            kwargs.pop('permission', 0),
            kwargs.pop('children', [])
        ]
        func_name:       str = ''
        func_line:       int = 0
        lines_to_remove: set = set()
        lines_to_sub_at: set[tuple[int, int]] = set()
        in_docstring:    bool = False
        doc_markers:     tuple[str, str] = ('"""', "'''")

        for i, line in enumerate(lines):
            simple = line.replace(' ', '').replace('\t', '').strip().lower()
            uncommented = line.strip().removeprefix('#')

            # If ''' or """ in line
            if True in (marker in line for marker in doc_markers):
                do_continue: bool = False
                for marker in doc_markers:

                    # When starting a docstring
                    if simple.startswith(marker) and not in_docstring:
                        try:
                            second_doc: int = simple.index(marker, simple.index(marker) + 1)
                        except ValueError:
                            # Multi-line docstring
                            in_docstring = True
                        else:
                            # Single-line docstring
                            lines_to_sub_at.add((i, second_doc + 3))
                        finally:
                            do_continue = True

                    # When ending a multi-line docstring
                    elif marker in simple and in_docstring:
                        in_docstring = False
                        lines_to_sub_at.add((i, line.index('"""') + 3))
                        do_continue = True

                if do_continue:
                    continue

            # If line is not currently in a multi-line string
            if not in_docstring:

                # If function hasn't yet been defined
                if not func_name:

                    if line.startswith('def'):
                        func_name = line.strip().removeprefix('def ').split('(')[0].replace('_', '-')
                        command_data[0] = func_name if not command_data[0] else command_data[0]
                        func_line = i
                        continue

                    # Remove all non-comment lines above function definition
                    if not simple.startswith('#'):
                        lines_to_remove.add(i)
                        continue

                    if simple.startswith('#children') and not command_data[4]:
                        try:
                            as_json = '{"data": ' + get_data(uncommented, 'children').translate(str.maketrans("'", '"')) + '}'
                            command_data[4] = json.loads(as_json)['data']
                        except (TypeError, ValueError):
                            pass
                        continue

                    for x, var in enumerate(('name', 'usage', 'description', 'permission')):
                        default = command_data[x]
                        if simple.startswith(f'#{var}') and not default:
                            try:
                                # Get string value and cast to type of default value
                                command_data[x] = type(default)(get_data(uncommented, var))
                            except TypeError:
                                pass
                            break

                else:
                    # Remove non-comment lines outside of function's scope
                    if simple != '' and not (line.startswith(' ') or line.startswith('\t')):
                        if not simple.startswith('#'):
                            lines_to_remove.add(i)

        if func_name:
            for i in lines_to_remove:
                # Mark lines for removal with a NULL char
                lines.insert(i, lines.pop(i) + '\0')

            for tup in lines_to_sub_at:
                # Substring all marked lines from start to specified index
                line_num, char_num = tup
                lines.insert(line_num, lines.pop(line_num)[:char_num] + '\n')

            lines = [line for line in lines if not line.endswith('\0')]
            # Replace function name with generic name 'command'
            lines.insert(func_line, lines.pop(func_line).strip().replace(f'def {func_name}', 'def command', 1) + '\n')

            new_data = {
                'name': command_data[0],
                'usage': command_data[1],
                'description': command_data[2],
                'permission': command_data[3],
                'function': True,
                'children': command_data[4],
                'overridable': True,
                'disabled': False
            }

            with open(f'{self.commands_path}/commands.json', encoding='utf8') as file:
                data: dict[str, Any] = json.load(file)

            commands = {command['name']: command for command in data.get('commands')}

            if commands.get(new_data['name'], {}).get('overridable') is not False:
                commands.update({new_data['name']: new_data})
            else:
                return ''

            data.update({'commands': list(commands.values())})

            with open(f'{self.commands_path}/commands.json', 'w', encoding='utf8') as commands_json, open(f'{self.commands_path}/zzz__{new_data["name"]}.py', 'w', encoding='utf8') as command_module:
                json.dump(data, commands_json, indent=2)
                command_module.writelines(lines)

            return new_data['name']

        return ''

    def remove_command(self, name: str) -> str:
        """Remove a command from commands.json and remove the associated python module.

        :param name: Name of command to remove.
        :return: {name} if successful, else empty string.
        """
        removed = False
        with open(f'{self.commands_path}/commands.json', encoding='utf8') as file:
            data: dict[str, Any] = json.load(file)

        commands = {command['name']: command for command in data.get('commands')}

        if commands.get(name, {}).get('overridable') is not False:
            if commands.pop(name, None) is not None:
                removed = True
        else:
            return ''

        data.update({'commands': list(commands.values())})

        with open(f'{self.commands_path}/commands.json', 'w', encoding='utf8') as file:
            json.dump(data, file, indent=2)

        try:
            os.remove(f'{self.commands_path}/zzz__{name}.py')
        except FileNotFoundError:
            pass
        else:
            removed = True

        return name if removed else ''
