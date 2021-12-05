###################################################################################################
#                              MIT Licence (C) 2021 Cubicpath@Github                              #
###################################################################################################
"""Exceptions for Dynamic Commands."""

from .models import *

__all__ = (
    'CommandError',
    'DisabledError',
    'ImproperUsageError',
    'NoPermissionError',
    'NotFoundError'
)


class CommandError(Exception):
    """General exception for command execution."""
    def __init__(self, command: Node, context: CommandContext, parent: Exception = None, message: str = None):
        self.command: Node = command
        self.context: CommandContext = context
        self.parent = parent
        super().__init__(f"'{context.source.display_name}' failed executing the '{command.name}' command." if message is None else message)


class DisabledError(CommandError):
    """Error when attempting to execute a disabled command."""
    def __init__(self, command: Node, context: CommandContext):
        super().__init__(command, context, self, f"'{command.name}' is disabled, enable to execute.")


class ImproperUsageError(CommandError):
    """Error for when a command is improperly used (manually triggered by command)."""
    def __init__(self, command: Node, context: CommandContext, message: str = None):
        super().__init__(command, context, self, f"Incorrect usage of '{command.name}'. To view usage information, use '!#prefix#!help {command.name}'." if message is None else message)


class NoPermissionError(CommandError):
    """Error for attempting to execute a command without required permissions."""
    def __init__(self, command: Node, context: CommandContext):
        super().__init__(command, context, self, f"'{context.source.display_name}' did not have the required permissions ({context.source.permission}/{command.permission}) to use the '{command.name}' command.")


class NotFoundError(CommandError):
    """Error executing a non-existent command name."""
    def __init__(self, command: Node, context: CommandContext):
        super().__init__(command, context, self, f"'{command.name}' is not a registered command.")
