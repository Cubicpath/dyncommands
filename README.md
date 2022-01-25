dyncommands
===============
Dynamic command execution, parsing, and storage.

------------------------------

[![Tests](https://img.shields.io/github/workflow/status/Cubicpath/dyncommands/Tests?logo=github&style=for-the-badge)][unittests]
[![Codecov](https://img.shields.io/codecov/c/gh/Cubicpath/dyncommands?label=Coverage&logo=codecov&style=for-the-badge)][coverage]
[![MIT License](https://img.shields.io/github/license/Cubicpath/dyncommands?style=for-the-badge)][license]

[![PyPI](https://img.shields.io/pypi/v/dyncommands?label=PyPI&logo=pypi&style=flat-square)][homepage]
[![Python](https://img.shields.io/pypi/pyversions/dyncommands?label=Python&logo=python&style=flat-square)][python]
[![CPython](https://img.shields.io/pypi/implementation/dyncommands?label=Impl&logo=python&style=flat-square)][python]

------------------------------
About:
---------------
Dyncommands allows you to dynamically import and run python functions. Useful for adding commands to IRC chatbots or CLI applications without a restart.

When parsing a string, it separates the command name from arguments, and executes the stored function with those arguments.
Each time the parser is called, you can pass in your own custom kwargs that the command will have access to.

All command modules are compiled through [RestrictedPython] before being allowed to run.
You can turn off Restricted execution by setting `CommandParser._unrestricted` to _true_, though this is highly discouraged when running untrusted code.

How to use:
---------------

### Short example:

```python
from pathlib import Path
from dyncommands import CommandParser, CommandContext, CommandSource

output: str = ''

def callback(text, *args):
    global output
    output = text

path = Path('path/to/directory')  # Must be a directory with a `commands.json` file in it
parser = CommandParser(path)  # Create the parser, which initializes using data located in the path directory
source = CommandSource(callback)  # Create a source, which is used to talk back to the caller

input_ = 'command-that-returns-wow arg1 arg2'  # this command would call zzz__command-that-returns-wow.py with arg1 and arg2

parser.parse(CommandContext(input_, source))  # Parse the new context and run the command and callback (If no errors occur)
assert output == 'wow'
```

### Command metadata:

Metadata for commands are stored in the `commands.json` file of the `CommandParser.commands_path` directory.
This is where all the data for the parser is loaded and stored.

All `commands.json` files are validated with [JSON Schemas][json-schema] through the [jsonschema][PyPIjsonschema] python package

#### commands.json [Draft-07] JSON Schema | [raw][schema-command]

| key             | type                 | description                                                                             | default  | required |
|-----------------|----------------------|-----------------------------------------------------------------------------------------|----------|----------|
| `commandPrefix` | _string_             | Strings must start with this prefix, otherwise it is ignored. Empty string accepts all. | **N/A**  | **Yes**  |
| `commands`      | _array_[**Command**] | Contains metadata for the stored command modules.                                       | **N/A**  | **Yes**  |

#### Command object [Draft-07] JSON Schema | [raw][schema-parser]

| key           | type                 | description                                                                                       | default  | required |
|---------------|----------------------|---------------------------------------------------------------------------------------------------|----------|----------|
| `name`        | _string_             | Uniquely identifies the command to the CommandParser.                                             | **N/A**  | **Yes**  |
| `usage`       | _string_             | Usage information (How to use args).                                                              | ""       | No       |
| `description` | _string_             | Description of command.                                                                           | ""       | No       |
| `permission`  | _integer_            | The permission level the CommandSource requires to run the command.                               | 0        | No       |
| `function`    | _boolean_, _null_    | Whether there is an associated python module to load.                                             | null     | No       |
| `children`    | _array_[**Command**] | Sub-commands; these are handled by the parent's function. (No associated modules for themselves). | []       | No       |
| `overridable` | _boolean_            | Whether the CommandParser can override any data inside this object (must be manually enabled).    | true     | No       |
| `disabled`    | _boolean_            | If **true** still load command, but raise a DisabledError when attempting to execute.             | false    | No       |

**NOTE:** Commands modules are not loaded unless they are listed in `commands.json` with the `function` key set to _true_.

#### Example `commands.json` contents:
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
there is a function defined as `command`. This function will be mapped to a `Command`'s function attribute
and stored in memory for execution. The function has access to any args that were parsed, as well as kwargs:

1. '**self**' (`Command`), which houses the metadata for the command that's being executed.

2. '**parser**' (`CommandParser`), which stores the list of registered commands and command data.

3. '**context**' (`CommandContext`), which supplies the `CommandSource` and the original text sent for parsing.

- Any custom kwargs passed to `CommandParser.parse(context: CommandContext, **kwargs)`.

Since commands cannot import their own modules, some are included in globals (`math`, `random`, and `string`).
Other attributes included in the global scope are: `getitem` (_operator.getitem_), and `ImproperUsageError` (_dyncommands.exceptions.ImproperUsageError_).

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

At any time, you can call `CommandParser.reload()` to reload all command modules and metadata from disk storage.

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

To add commands, you can either manually enter data into a `commands.json` file, or use the
`CommandParser.add_command(text: str, link: bool = False, **kwargs)` method.
The easiest way to use this method is to read the command module as text and pass that to the first argument.
You can also store command modules online to allow for remote installation, as setting the **link** parameter to **True**
will read **text** as a link, and will get the raw text data from that link. Ex: [gist] and [pastebin].

**NOTE:** When adding a command, metadata for 'name' **must** to be filled. This can be done in the form of comments.

Removing an already added command is relatively easy. Just call `CommandParser.remove_command(name: str)` with the name
of the command that you want to remove, and it will delete both the metadata and the command module from the disk.

If you don't want to delete the command when removing, a better alternative is to disable it with
`CommandParser.set_disabled(name: str, value: bool)`.

#### Example of metadata as in-line comments:
```python
# Name: points
# Usage: points [get (username:string) | set (username:string amount:integer)]
# Description: Get your current points
# Permission: 0
# Children: [{'name': 'get', 'usage': 'get (username:string)', 'permission':0}, {'name': 'set', 'usage': 'set (username:string amount:integer)', 'permission':500}]
def command(*args, **kwargs):
    ...
```

#### Examples of metadata as kwargs:
```python
parser = CommandParser('./')
with open('some_metadata.json') as _file:
    get_ = {'name': 'get', 'usage': 'get (username:string)', 'permission':0}
    set_ = {'name': 'set', 'usage': 'set (username:string amount:integer)', 'permission':500}
    children = [get_, set_]
    parser.add_command(_file.read(), name='my-command', description='Command with child commands.')
```
```python
parser = CommandParser('./')
with open('some_metadata.json') as _file:
    metadata = json.load(_file)
parser.add_command('https://gist.github.com/random/892hdh2fh389x0wcmksio7m', link=True, **metadata)
```

[coverage]: https://codecov.io/gh/Cubicpath/dyncommands "Codecov results"
[Draft-07]: https://tools.ietf.org/html/draft-handrews-json-schema-01 "Draft-07"
[gist]: https://gist.github.com "gist"
[homepage]: https://pypi.org/project/dyncommands/ "dyncommands PyPI"
[json-schema]: https://json-schema.org/ "json-schema.org"
[license]: https://choosealicense.com/licenses/mit "MIT License"
[pastebin]: https://pastebin.com "pastebin"
[PyPIjsonschema]: https://pypi.org/project/jsonschema/ "jsonschema PyPI"
[python]: https://www.python.org "Python"
[RestrictedPython]: https://github.com/zopefoundation/RestrictedPython "RestrictedPython GitHub"
[schema-command]: https://raw.githubusercontent.com/Cubicpath/dyncommands/master/src/dyncommands/schemas/command.schema.json# "Raw Command Schema"
[schema-parser]: https://raw.githubusercontent.com/Cubicpath/dyncommands/master/src/dyncommands/schemas/parser.schema.json# "Raw commands.json Schema"
[unittests]: https://github.com/Cubicpath/dyncommands/actions/workflows/tests.yaml "Test Results"
