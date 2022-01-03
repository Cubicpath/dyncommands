###################################################################################################
#                              MIT Licence (C) 2021 Cubicpath@Github                              #
###################################################################################################
"""Dynamic command execution, parsing, and storage.

----------

Dynamically-loaded commands are denoted by filename with a prefix of "zzz__". Inside a command module,
there is a function defined as "command". This function will be mapped to a :py:attr:`Command.function` attribute
to be stored in memory for execution. The function has access to any args that were parsed, as well as kwargs:

* 'self' (:py:class:`Command`), which houses the metadata for the command that's being executed.

* 'parser' (:py:class:`CommandParser`), which stores the list of registered :py:class:`Command`s and :py:class:`CommandData`.

* 'context' (:py:class:`CommandContext`), which supplies the :py:class:`CommandSource` and the original text sent for parsing.

* Any custom kwargs passed to :py:class:`CommandParser`.parse().

----------

Command modules are compiled through :py:mod:`RestrictedPython` before execution, and are therefor heavily limited in namespace.
Modules included in :py:func:`globals` are: :py:mod:`math`, :py:mod:`random`, and :py:mod:`string`.
Use :py:func:`operator.getitem` instead of subscripts, and :py:exc:`ImproperUsageError` for all manually-triggered command errors.

----------

`Example function <https://gist.github.com/Cubicpath/8cafed94908b74b370ecd3960fbca3b0>`_ that takes in 2 arguments and
them to roll dice and sends the output of the roll to the source.

"""
from ._version import __version__
from ._version import __version_info__
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
