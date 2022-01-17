###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
# noinspection PyUnresolvedReferences
# Name: test
# Usage: test [*args:Any]
# Description: Test command.
# Permission: 500
def command(*_, **kwargs):
    context = kwargs.pop('context')
    return f"'{context.working_string.strip()}' is correct usage of the 'test' command."
