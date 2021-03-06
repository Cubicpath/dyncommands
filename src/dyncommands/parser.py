###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Main command parser module for Dynamic Commands."""
import json
import operator
from collections.abc import Callable
from pathlib import Path
from platform import python_implementation as _impl
from typing import Any
from typing import Optional
from typing import Union
from warnings import warn

if _impl() == 'CPython':
    from RestrictedPython.compile import compile_restricted as safe_compile  # isort:skip
    from RestrictedPython.transformer import RestrictingNodeTransformer  # isort:skip
    from RestrictedPython.Eval import default_guarded_getitem  # isort:skip
    from RestrictedPython.Eval import default_guarded_getiter  # isort:skip
    from RestrictedPython.Guards import guarded_iter_unpack_sequence  # isort:skip
    from RestrictedPython.Guards import guarded_unpack_sequence  # isort:skip
    from RestrictedPython.Guards import safer_getattr  # isort:skip
    from RestrictedPython.Guards import safe_builtins  # isort:skip
    from RestrictedPython.Limits import limited_builtins  # isort:skip
    from RestrictedPython.Utilities import utility_builtins  # isort:skip
else:
    warn(ImportWarning('RestrictedPython is not supported on non-CPython implementations, and will not be imported.'))  # pragma: no cover

from .exceptions import *
from .models import *
from .schemas import *
from .utils import *

__all__ = (
    'Command',
    'CommandParser',
)

if _impl() == 'CPython':
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


# noinspection PyProtectedMember
class Command(Node):
    """Dynamic command object. Created on demand by a :py:class:`CommandParser`."""
    __slots__ = ('_function',)

    def __init__(self, data: Optional[CommandData], parser: 'CommandParser') -> None:
        """Build :py:class:`Command` from :py:class:`ParserData` and matching zzz__ modules."""
        super().__init__()
        self._function: Callable = DUMMY_FUNC
        if data is not None:
            self.name = data.name  # String; required
            self.usage = data.usage  # String
            self.description = data.description  # String
            self.permission = data.permission  # Integer; min of -1
            self.children = CaseInsensitiveDict({props.name: Node(parent=self, **props) for props in data.children})
            self.disabled = data.disabled  # Boolean

            if data.function is True:  # True, False, and None
                parser._load_module(self)

    def __call__(self, *args, **kwargs) -> Optional[str]:
        """Syntax sugar for :py:method:`Command._execute`."""
        return self._execute(*args, **kwargs)

    def _execute(self, *args, **kwargs) -> Optional[str]:
        """:py:class:`Command` (or last :py:class:`Node`)'s permission must be at least 0 and equal to or less than
        the :py:class:`CommandSource`'s permission level.

        Note: an argument with a permission property set to 0 will always run, regardless of the base command's permissions.

        :raises CommandError: If any exceptions are caught during.
        :raises DisabledError: When command specified in the contextual working string is disabled.
        :raises NoPermissionError: When contextual source does not have the required permissions.
        """
        context: CommandContext = kwargs['context']
        parser: CommandParser = kwargs['parser']
        kwargs['self'] = self

        final_node: Node = self
        for arg in args:
            final_node = final_node.children.get(arg, final_node)

        if not self.disabled and not final_node.disabled:
            # Get permission level of last argument with properties, or the command itself if no args with properties
            if context.source.has_permission(final_node.permission) or parser._ignore_permission:
                if not parser._unrestricted:
                    # Proxy public attributes of kwargs; exclude Path attributes
                    kwargs = {kwarg: PrivateProxy(kwval, parser._should_hide_attr) for kwarg, kwval in kwargs.items()}
                try:
                    return self._function(*args, **kwargs)
                except Exception as e:
                    raise CommandError(self, context, e) from e

            raise NoPermissionError(final_node, context)
        raise DisabledError(self, context)


class CommandParser:
    """Keeps track of all commands and command metadata. Allows for dynamic execution of commands through string parsing."""

    def __init__(self, commands_path: Union[str, Path], silent: bool = False, ignore_permission: bool = False, unrestricted: Union[bool, None] = None) -> None:
        """Create a new Parser and load all command data from the given path.

        :param silent: If true, stops all debug printing.
        :param ignore_permission: If true, permission level is not taken into account when executing a command.
        :param unrestricted: If true, disables RestrictedPython compilation of command modules. Defaults to True when running on non-CPython implementations.
        """
        if unrestricted is None:
            unrestricted = False if _impl() == 'CPython' else True

        self.commands:            CaseInsensitiveDict[Command] = CaseInsensitiveDict()
        self.command_data:        list[CommandData] = []
        self.path:                Path = Path(commands_path)
        self._command_prefix:     str = '/'
        self._current_command:    Optional[Command] = None
        self._delimiting_str:     str = ' '
        self._ignore_permission:  bool = ignore_permission
        self._silent:             bool = silent
        self._unrestricted:       bool = unrestricted

        if self._unrestricted:
            warn(UnrestrictedWarning(f'UNRESTRICTED MODE ON FOR {self.__repr__()} AT {self.path}. DO NOT RUN UNTRUSTED CODE.'))

        self.reload()

    def __call__(self, context: CommandContext, **kwargs) -> None:
        """Syntax sugar for self.parse."""
        self.parse(context=context, **kwargs)

    @property
    def prefix(self) -> str:
        """:return: The current prefix needed to recognize if the given string is a command."""
        return self._command_prefix

    @prefix.setter
    def prefix(self, value) -> None:
        """Set the current prefix both in memory and in the commands.json file."""
        json_path: Path = self.path / 'commands.json'
        self._command_prefix = value
        with json_path.open(mode='r', encoding='utf8') as file:
            new_json: dict[str, Any] = json.load(file)
            new_json['commandPrefix'] = self._command_prefix
        with json_path.open(mode='w', encoding='utf8') as file:
            json.dump(new_json, file, indent=2)

    # pylint: disable=exec-used
    def _load_module(self, command: Command) -> None:
        """Loads a command's respective python code from storage."""
        module_path: Path = self.path / f'zzz__{command.name}.py'
        locals_:     dict[str, Any] = {}

        try:
            with module_path.open(mode='r', encoding='utf8') as file:
                # Attempt to compile code and run function definition
                plaintext_code = file.read()
                if not self._unrestricted:
                    # Restricted
                    byte_code = safe_compile(plaintext_code, filename=str(module_path), mode='exec', policy=_CommandPolicy)
                    exec(byte_code, command_globals, locals_)
                else:
                    # Unrestricted
                    globals_ = globals().copy()
                    globals_.update(__file__=str(module_path), __package__=None)
                    byte_code = compile(plaintext_code, filename=str(module_path), mode='exec')
                    exec(byte_code, globals_, locals_)

        except (FileNotFoundError, SyntaxError, NotImplementedError) as e:
            self.print(str(e))
            self.print(f"Discarding broken command '{command.name}' from {module_path}.")
            self.remove_command(command.name)

        else:
            self.print(f"Loading file {module_path} from disk into '{command.name}'.")
            command._function = locals_.get('command', DUMMY_FUNC)

    def _should_hide_attr(self, name: str, o: Any) -> bool:
        if self._unrestricted:
            return False

        # Include already proxied objects
        return not isinstance(o, PrivateProxy) and (
                isinstance(o, Path) or  # Exclude Path attributes
                name.startswith('_')    # Exclude protected attributes
        )

    def reload(self) -> None:
        """Load all data from the commands.json file in the commands_path.
        For every :py:class:`CommandData` object in the :py:class:`ParserData`, a :py:class:`Command` object is constructed and assigned with the same name.

        :raises FileNotFoundError: If parser cannot find the commands.json file
        """
        json_path: Path = self.path / 'commands.json'

        if json_path.exists():
            with json_path.open(mode='r', encoding='utf8') as file:
                json_data: ParserData = ParserData(json.load(file))
                json_data.validate(json_data)

            self._command_prefix = json_data.commandPrefix
            self.command_data = json_data.commands
            self.commands = CaseInsensitiveDict({command.name: Command(command, self) for command in self.command_data})

        else:
            raise FileNotFoundError(f'commands.json not in commands_path ({self.path})')

    def parse(self, context: CommandContext, **kwargs) -> None:
        """Parse a :py:class:`CommandContext`'s working_string for commands and arguments, then execute them.

        It is EXTREMELY recommended wrapping this function in a try-except block.

        :param context: Command context for parsing.
        :param kwargs: kwargs you want to  Command being parsed to have access to during execution.
        :raises DisabledError: When command specified in the contextual working string is disabled.
        :raises ImproperUsageError: Manually triggered exception from the command itself.
        :raises NoPermissionError: When contextual source does not have the required permissions.
        :raises NotFoundError: When command specified in the contextual working string is not found in the command data.
        """

        input_: str = context.working_string.removeprefix(self.prefix).rstrip('\U000e0000').strip()
        if input_:
            split: list[str] = input_.split(self._delimiting_str)
            name, args = split[0], split[1:]
            if self.commands.get(name) is not None:
                kwargs.update({'context': context, 'parser': self})
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
                        message: str = str(e.parent)
                        if message:
                            context.source.send_feedback(message.replace('!#prefix#!', self.prefix), context.source.display_name)
                    if isinstance(e.parent, CommandError):
                        raise e.parent from e
            else:
                raise NotFoundError(name, context)

    def print(self, *values: object, sep: Optional[str] = None, end: Optional[str] = None, file: Optional[object] = None, flush: bool = False) -> None:
        """Print if not self._silent."""
        if not self._silent:
            print(*values, sep=sep, end=end, file=file, flush=flush)

    def set_disabled(self, command_name: str, value: bool) -> bool:
        """Set a :py:class:`Command` as disabled.

        :param command_name: Command to disable.
        :param value: Whether disabled or not.
        :return: If disabled state successfully changed.
        """
        json_path: Path = self.path / 'commands.json'

        with json_path.open(mode='r', encoding='utf8') as file:
            data:     ParserData = ParserData(json.load(file))
            commands: dict[str, CommandData] = {command.name: command for command in data.commands}

            if commands.get(command_name, CommandData.empty()).overridable is not False:
                commands[command_name].disabled = value
                self.commands.get(command_name).disabled = value
            else:
                return False

            data.commands = list(commands.values())

        with json_path.open(mode='w', encoding='utf8') as file:
            json.dump(data, file, indent=2)

        return True

    def add_command(self, text: str, link: bool = False, **kwargs) -> str:
        """Adds a :py:class:`Command` using data read from {text}. Command metadata must either be passed in through a kwarg,
        or structured as an inline python comment above the command function.

        ---------------------------------------

        Example of passing metadata inline::

            # Name: do-nothing
            # Usage: do-nothing [amount:integer sides:integer]
            # Description: Rolls die.
            # Permission: 0
            def command(*args, **kwargs):
                pass

        ---------------------------------------

        Example of passing metadata over kwargs::

            parser = CommandParser('./')
            with open('some_metadata.json') as _file:
                metadata = json.load(_file)
            parser.add_command('https://gist.github.com/random/892hdh2fh389x0wcmksio7m', link=True, **metadata)

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
            simple:      str = line.replace(' ', '').replace('\t', '').strip().lower()
            uncommented: str = line.strip().removeprefix('#')

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
                            lines_to_sub_at.add((i, second_doc + len(marker)))
                        finally:
                            do_continue = True

                    # When ending a multi-line docstring
                    elif marker in simple and in_docstring:
                        in_docstring = False
                        lines_to_sub_at.add((i, line.index(marker) + len(marker)))
                        do_continue = True

                if do_continue:
                    continue

            # If line is not currently in a multi-line docstring
            if not in_docstring:

                # If function hasn't yet been defined
                if not func_name:

                    if line.startswith('def'):
                        func_name = line.strip().removeprefix('def ').split('(')[0].replace('_', '-')
                        command_data[0] = func_name if not command_data[0] else command_data[0]
                        func_line = i
                        continue

                    # Remove all non-comment/empty lines above function definition
                    if simple and not simple.startswith('#'):
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
                        default: Any = command_data[x]
                        if simple.startswith(f'#{var}') and not default:
                            try:
                                # Get string value and cast to type of default value
                                command_data[x] = type(default)(get_data(uncommented, var))
                            except (TypeError, ValueError):
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
                lines.insert(i, lines.pop(i).replace('\n', '\0\n'))

            for tup in lines_to_sub_at:
                # Substring all marked lines from start to specified index
                line_num, char_num = tup
                lines.insert(line_num, lines.pop(line_num)[:char_num] + '\n')

            lines = [line for line in lines if not line.endswith('\0')]
            # Replace function name with generic name 'command'
            lines.insert(func_line, lines.pop(func_line).strip().replace(f'def {func_name}', 'def command', 1) + '\n')

            new_data: CommandData = CommandData(
                name=command_data[0],
                usage=command_data[1],
                description=command_data[2],
                permission=command_data[3],
                function=True,
                children=command_data[4],
                overridable=True,
                disabled=False
            )

            json_path:   Path = self.path / 'commands.json'
            module_path: Path = self.path / f'zzz__{new_data.name}.py'

            with json_path.open(mode='r', encoding='utf8') as json_file:
                data: ParserData = ParserData(json.load(json_file))

            commands: dict[str, CommandData] = {command.name: command for command in data.commands}

            if commands.get(new_data.name, CommandData.empty()).overridable is not False:
                commands[new_data.name] = new_data
            else:
                return ''

            data.commands = list(commands.values())

            with json_path.open(mode='w', encoding='utf8') as json_file, module_path.open(mode='w', encoding='utf8') as module_file:
                json.dump(data, json_file, indent=2)
                json_file.write('\n')
                module_file.writelines(lines)

            self.command_data = data.commands
            self.commands[new_data.name] = Command(commands[new_data.name], self)

            return new_data.name

        return ''

    def remove_command(self, name: str) -> str:
        """Remove a :py:class:`CommandData` from commands.json and remove the associated python module.

        :param name: Name of command to remove.
        :return: {name} if successful, else empty string.
        """
        json_path:   Path = self.path / 'commands.json'
        module_path: Path = self.path / f'zzz__{name}.py'

        with json_path.open(mode='r', encoding='utf8') as file:
            data: ParserData = ParserData(json.load(file))

        commands: dict[str, CommandData] = {command.name: command for command in data.commands}

        if commands.get(name, CommandData.empty()).overridable is False:
            return ''

        removed: bool = commands.pop(name, None) is not None
        data.commands = list(commands.values())

        with json_path.open(mode='w', encoding='utf8') as file:
            json.dump(data, file, indent=2)

        try:
            module_path.unlink()
        except FileNotFoundError:
            pass
        else:
            removed = True

        if removed:
            self.command_data = data.commands
            self.commands.pop(name, None)
            return name

        return ''
