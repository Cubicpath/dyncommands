dyncommands
===============
Dynamic command execution, parsing, and storage.

------------------------------

[![Tests](https://img.shields.io/github/workflow/status/Cubicpath/dyncommands/Tests?logo=github&style=for-the-badge)](https://github.com/Cubicpath/dyncommands/actions/workflows/tests.yaml)
[![Codecov](https://img.shields.io/codecov/c/gh/Cubicpath/dyncommands?label=Coverage&logo=codecov&style=for-the-badge)](https://codecov.io/gh/Cubicpath/dyncommands)
[![MIT License](https://img.shields.io/github/license/Cubicpath/dyncommands?style=for-the-badge)](https://choosealicense.com/licenses/mit)

[![PyPI](https://img.shields.io/pypi/v/dyncommands?label=PyPI&logo=pypi&style=flat-square)](https://pypi.org/project/dyncommands/)
[![Python](https://img.shields.io/pypi/pyversions/dyncommands?label=Python&logo=python&style=flat-square)](https://python.org)
[![CPython](https://img.shields.io/pypi/implementation/dyncommands?label=Impl&logo=python&style=flat-square)](https://python.org)

------------------------------
About:
---------------
Dyncommands allows you to dynamically import and run python functions. Useful for adding commands to IRC chatbots or CLI applications without a restart.

When parsing a string, it separates the command name from arguments, and executes the stored function with those arguments.
Each time the parser is called, you can pass in your own custom kwargs that the command will have access to.

All command modules are compiled through [RestrictedPython](https://github.com/zopefoundation/RestrictedPython) before being allowed to run.

How to use:
---------------

### Command metadata:
Metadata for commands are stored in the commands.json file inside the _commands_path_ of the parser.
This is where all the data for the parser is loaded or stored.

There are two top-level keys:
- __commandPrefix__: _str_
  - String being parsed must start with this string, otherwise it is ignored. Empty string accepts all.
- __commands__: _array[object]_
  - Contains command objects

Available metadata keys for objects inside the __commands__ array are:

| key             | type          | description                                                                                       |
|-----------------|---------------|---------------------------------------------------------------------------------------------------|
| name (Required) | string        | Uniquely identifies the command to the CommandParser.                                             |
| usage           | string        | Usage information (How to use args)                                                               |
| description     | string        | Description of command                                                                            |
| permission      | integer       | The permission level the CommandSource requires to run the command.                               |
| function        | boolean       | Whether there is an associated python module to load.                                             |
| children        | array[object] | Sub-commands; these are handled by the parent's function. (No associated modules for themselves). |
| overridable     | boolean       | Whether the CommandParser can override any data inside this object (must be manually enabled).    |
| disabled        | boolean       | If __true__ still load command, but raise a DisabledError when attempting to execute.             |

__NOTE:__ Commands modules are not loaded unless they are listed in commands.json with the "function" key set to true.

#### Example commands.json contents:
```json
{
  "commandPrefix": "!",
  "commands": [
    {
      "name": "test",
      "usage": "test [*args:any]",
      "description": "Test command.",
      "permission": 500,
      "function": true
    },
    {
      "name": "test2",
      "function": false
    }
  ]
}
```

### Command modules:

Dynamically-loaded commands are denoted by filename with a prefix of "zzz__". Inside a command module,
there is a function defined as "command". This function will be mapped to a Command's function attribute
and stored in memory for execution. The function has access to any args that were parsed, as well as kwargs:

1. 'self' (Command), which houses the metadata for the command that's being executed.

2. 'parser' (CommandParser), which stores the list of registered commands and command data.

3. 'context' (CommandContext), which supplies the CommandSource and the original text sent for parsing.

- Any custom kwargs passed to CommandParser.parse.

Since commands cannot import heir own modules, some are included in globals (math, random, and string).

#### Example command module:
```python
def command(*args, **kwargs):
    self, context = kwargs.pop('self'), kwargs.pop('context')
    source = context.source
    if len(args) == 2:
        amount, sides = abs(int(getitem(args, 0))), abs(int(getitem(args, 1)))
        if amount > 0 and sides > 0:
            dice_rolls = [f"{(str(i + 1) + ':') if amount > 1 else ''} {str(random.randint(1, sides))}/{sides}" for i in range(amount)]
            source.send_feedback(f"/me \U0001f3b2 {source.display_name} rolled {'a die' if amount == 1 else str(amount) + ' dice'} with {sides} side{'' if sides == 1 else 's'}: {', '.join(dice_rolls)} \U0001f3b2")
        else:
            raise ImproperUsageError(self, context)
    else:
        raise ImproperUsageError(self, context)
```

At any time, you can call CommandParser.reload() to reload all command modules and metadata from disk storage.

#### Example file structure:
    ../
    │
    ├───[commands_path]/
    │       ├─── commands.json
    │       ├─── zzz__[command1].py
    │       ├─── zzz__[command2].py
    │       └─── zzz__[command3].py
    │

### Adding/Removing Commands:

To add commands, you can either manually enter data into a commands.json file, or use the
CommandParser.add_command(__text__: _str_, __link__: _bool = False_, __**kwargs__) method.
The easiest way to use this method is to read the command module as text and pass that to the first argument.
You can also store command modules online to allow for remote installation, as setting the __link__ parameter to __True__
will read __text__ as a link, and will get the raw text data from that link. Ex: gist and pastebin.

__NOTE:__ When adding a command, metadata for 'name' __must__ to be filled. This can be done in the form of comments.


#### Example of metadata as comments:
```python
# Name: points
# Usage: points [get (username:string)| set (username:string amount:integer)]
# Description: Get your current points
# Permission: 0
# Children: [{'name': 'get', 'usage': 'get (username:string)', 'permission':0}, {'name': 'set', 'usage': 'set (username:string amount:integer)', 'permission':500}]
def command(*args, **kwargs):
    ...
```

Removing an already added command is relatively easy. Just call CommandParser.remove_command(__name__: _str_) with the name
of the command that you want to remove, and it will delete both the metadata and the command module from the disk.

If you don't want to delete the command when removing, a better alternative is to disable it with
CommandParser.set_disabled(__name__: _str_, __value__: _bool_).
