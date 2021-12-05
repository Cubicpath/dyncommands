###################################################################################################
#                              MIT Licence (C) 2021 Cubicpath@Github                              #
###################################################################################################
# noinspection PyUnresolvedReferences
def command(*args, **kwargs):
    context = kwargs.pop('context')
    return f"'{context.working_string.strip()}' is correct usage of the 'test' command."
