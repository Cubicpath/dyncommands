###################################################################################################
#                              MIT Licence (C) 2021 Cubicpath@Github                              #
###################################################################################################
# noinspection PyUnresolvedReferences
# Name: commands
# Children: [{"name": "good", "permission": 0}, {"name": "bad", "permission": Bad-Value}]

def command(*args, **kwargs):
    self, parser, context = (
        kwargs.pop('self'),
        kwargs.pop('parser'),
        kwargs.pop('context')
    )
    source = context.source
    if len(args) == 0:
        source.send_feedback(f"Your available commands are: {', '.join([name for name in {name: cmd for name, cmd in parser.commands.items() if source.has_permission(cmd.permission) and not cmd.disabled}])}", to=source.display_name)
    elif len(args) == 1 and getitem(args, 0) == 'reload':
        parser.reload()
        source.send_feedback("Parser data has been synced with new data!", to=source.display_name)
    elif len(args) == 2 and getitem(args, 0) == 'add':
        link = getitem(args, 1)
        name = parser.add_command(link, link=True)
        if name:
            source.send_feedback(f"Command '{name}' added. Reload command data to take effect.", to=source.display_name)
    elif len(args) == 2 and getitem(args, 0) == 'disable':
        command_name = getitem(args, 1)
        source.send_feedback(f"Command '{command_name}' {'could not be' if not parser.set_disabled(command_name, True) else ''} disabled.", to=source.display_name)
    elif len(args) == 2 and getitem(args, 0) == 'enable':
        command_name = getitem(args, 1)
        source.send_feedback(f"Command '{command_name}' {'could not be' if not parser.set_disabled(command_name, False) else ''} enabled.", to=source.display_name)
    elif len(args) == 2 and getitem(args, 0) == 'remove':
        command_name = getitem(args, 1)
        if parser.remove_command(command_name):
            source.send_feedback(f"Command '{command_name}' removed. Reload command data to take effect.", to=source.display_name)
    else:
        raise ImproperUsageError(self, context)
