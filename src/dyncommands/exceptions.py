###################################################################################################
#                              MIT Licence (C) 2021 Cubicpath@Github                              #
###################################################################################################
"""Exceptions raised during parsing."""
from typing import Optional

from .models import *

__all__ = (
    'CommandError',
    'DisabledError',
    'ImproperUsageError',
    'NoPermissionError',
    'NotFoundError'
)


class CommandError(Exception):
    """General exception for :py:class:`Node` execution."""
    def __init__(self, command: Optional[Node], context: CommandContext, parent: Exception = None, message: str = None) -> None:
        self.command: Optional[Node] = command
        self.context: CommandContext = context
        self.parent = parent
        name = command.name if command else 'Unknown'
        super().__init__(f"'{context.source.display_name}' failed executing the '{name}' command." if message is None else message)


class DisabledError(CommandError):
    """Error when attempting to execute a disabled :py:class:`Node`."""
    def __init__(self, command: Node, context: CommandContext) -> None:
        super().__init__(command, context, self, f"'{command.name}' is disabled, enable to execute.")


class ImproperUsageError(CommandError):
    """Error for when a :py:class:`Node` is improperly used (manually triggered by :py:class:`Node`)."""
    def __init__(self, command: Node, context: CommandContext, message: str = None) -> None:
        super().__init__(command, context, self, f"Incorrect usage of '{command.name}'. To view usage information, use '!#prefix#!help "
                                                 f"{command.name}'." if message is None else message)


class NoPermissionError(CommandError):
    """Error for attempting to execute a :py:class:`Node` without required permissions."""
    def __init__(self, command: Node, context: CommandContext) -> None:
        super().__init__(command, context, self, f"'{context.source.display_name}' did not have the required permissions "
                                                 f"({context.source.permission}/{command.permission}) to use the '{command.name}' command.")


class NotFoundError(CommandError):
    """Error executing a non-existent :py:class:`Node` name."""
    def __init__(self, name: str, context: CommandContext) -> None:
        super().__init__(None, context, self, f"'{name}' is not a registered command.")
