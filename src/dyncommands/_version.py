###################################################################################################
#                              MIT Licence (C) 2021 Cubicpath@Github                              #
###################################################################################################
"""Version information."""
# Store the version here so:
# 1) We don't load dependencies by storing it in __init__.py
# 2) We can load it in setup.cfg
# 3) We can import it into modules

__version_info__ = (1, 0, 2, 'candidate', 0)
"""Major, Minor, Micro, Release level, Serial in respective order."""


def _stringify(major: int, minor: int, micro: int = 0, releaselevel: str = 'final', serial: int = 0) -> str:
    """Stringifies a version number based on version info given.

    Releaselevel is the status of the given version, NOT the project itself.
    All versions of an alpha or beta should be a 'final' releaselevel.

    Serial is only taken into account if releaselevel is not 'final' or 'release',
    you may also use your own custom releaselevel strings,
    though they will be shortened if they are longer than 3 characters.

    Ex: (1, 0) -> 1.0.0
    Ex: (0, 3, 2, 'beta') -> 0.3.2b
    Ex: (1, 0, 0, 'release') -> 1.0.0
    Ex: (3, 10, 0, 'candidate', 0) -> 3.10.0rc
    Ex: (3, 9, 1, 'alpha', 3) -> 3.9.2a3

    :param major: First and most important version number.
    :param minor: Second and less important version number.
    :param micro: Last and least important version number.
    :param releaselevel: Status of current version.
    :param serial: Separate version number of an Alpha/Beta for an upcoming release version.
    :return: String representation of version number.
    """
    v_number: str = f'{major}.{minor}.{micro}'
    if releaselevel and releaselevel not in ('final', 'release'):
        if releaselevel == 'candidate':
            releaselevel = 'rc'
        v_number += releaselevel if len(releaselevel) <= 3 else releaselevel[0]
        v_number += str(serial) if serial else ''
    return v_number


__version__ = _stringify(*__version_info__)
"""String representation of version number."""
