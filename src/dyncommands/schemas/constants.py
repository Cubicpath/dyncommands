###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Neutral namespace for constants."""

__all__ = (
    'NOT_FOUND',
    'SCHEMA_DEFAULT',
)

NOT_FOUND: ... = object()
"""Used to tell difference from None and Not Found using object identities"""

SCHEMA_DEFAULT: ... = object()
"""Used to signal to a SchemaHolder to use the schema's default value if the value is not found."""
