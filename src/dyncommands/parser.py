###################################################################################################
#                              MIT Licence (C) 2021 Cubicpath@Github                              #
###################################################################################################
"""Parser for Dynamic Commands."""

import operator
import os
import json
from typing import Any, Optional
from RestrictedPython import RestrictingNodeTransformer, safe_builtins, limited_builtins, utility_builtins, compile_restricted as safe_compile
from RestrictedPython.Eval import default_guarded_getiter, default_guarded_getitem
from RestrictedPython.Guards import guarded_unpack_sequence, guarded_iter_unpack_sequence, safer_getattr

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
                self.children = {props['name']: Node(parent=self, **props) for props in command.get('children', [])}
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
            with open(file_path, 'r', encoding='utf8') as file:
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
        with open(f'{self.commands_path}/commands.json', 'r', encoding='utf8') as file:
            new_json: dict[str, Any] = json.load(file)
            new_json['commandPrefix'] = self._command_prefix
        with open(f'{self.commands_path}/commands.json', 'w', encoding='utf8') as file:
            json.dump(new_json, file, indent=2)

    def reload(self) -> None:
        """Load all data from the commands.json file in the commands_path.
        For every command JSON object, a Command object is constructed and assigned with the same name.
        """
        with open(f'{self.commands_path}/commands.json', 'r', encoding='utf8') as file:
            json_data = json.load(file)

        self._command_prefix = json_data['commandPrefix']
        self.command_data = json_data['commands']
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
        with open(f'{self.commands_path}/commands.json', 'r', encoding='utf8') as file:
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
        name, usage, description, permission, children = (
            kwargs.pop('name', ''),
            kwargs.pop('usage', ''),
            kwargs.pop('description', ''),
            kwargs.pop('permission', 0),
            kwargs.pop('children', [])
        )
        func_name:       str = ''
        func_line:       int = 0
        lines_to_remove: set = set()
        for i, line in enumerate(lines):
            l0 = line.replace(' ', '').replace('\t', '').lower()
            l1 = line.strip().removeprefix('#')

            if l0.startswith('def'):
                func_name = line.strip().removeprefix('def ').split('(')[0].replace('_', '-')
                name = func_name if not name else name
                func_line = i
                break

            if not (l0.startswith('#')
                    or l0.startswith("'''")
                    or l0.endswith("'''")
                    or l0.startswith('"""')
                    or l0.endswith('"""')
            ): lines_to_remove.add(i)

            elif l0.startswith('#children') and not children:
                try:
                    as_json = '{"data": ' + get_data(l1, 'children').translate(str.maketrans('\'', '"')) + '}'
                    children = json.loads(as_json)['data']
                except (TypeError, ValueError):
                    pass

            else:
                for var in ('name', 'usage', 'description', 'permission'):
                    default = vars()[var]
                    if l0.startswith(f'#{var}' and not default):
                        try:
                            # Get string value and cast to type of default value
                            vars()[var] = type(default)(get_data(l1, var))
                        except TypeError:
                            pass

        if func_name:
            for i in lines_to_remove:
                lines.insert(i, lines.pop(i) + '\0')
            lines = [line for line in lines if not line.endswith('\0')]
            # Replace function name with generic name 'command'
            lines.insert(func_line, lines.pop(func_line).strip().replace(f'def {func_name}', 'def command', 1) + '\n')

            new_data = {
                'name': name,
                'usage': usage,
                'description': description,
                'permission': permission,
                'function': True,
                'children': children,
                'overridable': True,
                'disabled': False
            }

            with open(f'{self.commands_path}/commands.json', 'r', encoding='utf8') as file:
                data: dict[str, Any] = json.load(file)

            commands = {command['name']: command for command in data.get('commands')}

            if commands.get(name, {}).get('overridable') is not False:
                commands.update({name: new_data})
            else:
                return ''

            data.update({'commands': list(commands.values())})

            with open(f'{self.commands_path}/commands.json', 'w', encoding='utf8') as file:
                json.dump(data, file, indent=2)

            with open(f'{self.commands_path}/zzz__{name}.py', 'w', encoding='utf8') as file:
                file.writelines(lines)
                file.write('\n')
            return name

        return ''

    def remove_command(self, name: str) -> str:
        """Remove a command from commands.json and remove the associated python module.

        :param name: Name of command to remove.
        :return: {name} if successful, else empty string.
        """
        removed = False
        with open(f'{self.commands_path}/commands.json', 'r', encoding='utf8') as file:
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
