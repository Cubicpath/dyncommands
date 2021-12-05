###################################################################################################
#                              MIT Licence (C) 2021 Cubicpath@Github                              #
###################################################################################################
"""Dynamic command execution, parsing, and storage.

----------

Dynamically-loaded commands are denoted by filename with a prefix of "zzz__". Inside a python command file,
there is a function defined as "command". This function will be mapped to a dyncommands.parser.Command's function attribute
and stored in memory for execution. The function has access to any args that were parsed, as well as kwargs:

-1. 'self' (Command), which houses the metadata for the command that's being executed.

-2. 'parser' (CommandParser), which stores the list of registered commands and command data.

-3. 'context' (CommandContext), which supplies the CommandSource and the original text sent for parsing.

-X. Any custom kwargs passed to CommandParser.parse.

----------

Commands are compiled through RestrictedPython before execution, and are therefor heavily limited in namespace.
Modules included in globals() are: math, random, and string. Use getitem instead of subscripts, and ImproperUsageError for
all manually-triggered command errors.

----------

Example function that takes in 2 arguments and uses them to roll dice and sends the output of the roll to the source:

https://gist.github.com/Cubicpath/8cafed94908b74b370ecd3960fbca3b0

"""

from ._version import __version__, __version_info__
from .exceptions import *
from .models import *
from .parser import *

__all__ = (
    'CaseInsensitiveDict',
    'Command',
    'CommandError',
    'CommandContext',
    'CommandParser',
    'CommandSource',
    'DisabledError',
    'ImproperUsageError',
    'Node',
    'NoPermissionError',
    'NotFoundError'
)

__author__ = 'Cubicpath@Github <cubicpath@pm.me>'
