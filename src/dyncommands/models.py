###################################################################################################
#                              MIT Licence (C) 2021 Cubicpath@Github                              #
###################################################################################################
"""Models for Dynamic Commands."""

from typing import Optional, Union, Any
from collections.abc import Callable

from requests.structures import CaseInsensitiveDict

from .utils import DUMMY_FUNC


__all__ = (
    'CaseInsensitiveDict',
    'CommandContext',
    'CommandSource',
    'Node'
)


class Node:
    """Common object that stores metadata and child nodes."""
    __slots__ = ('_parent', '_name', 'usage', 'description', 'permission', 'children', 'disabled')

    def __init__(self, **kwargs):
        """Initialize and load any kwargs as attributes.

        Supported kwargs are:
        :keyword parent: (Node).
        :keyword name: (str) Uniquely identifies this node to its parent.
        :keyword usage: (str) Metadata.
        :keyword description: (str) Metadata.
        :keyword permission: (int) Permission required to use this Node.
        :keyword children: (Iterable[Dict[str, Any]]) Creates children nodes for every dictionary dataset given.
        :keyword disabled: (bool) Metadata.
        :raises ValueError: For unexpected kwargs
        """
        self._parent:       Optional['Node'] = kwargs.pop('parent', None)
        self._name:         str = kwargs.pop('name', '')
        self.usage:         str = kwargs.pop('usage', '')
        self.description:   str = kwargs.pop('description', '')
        self.permission:    int = kwargs.pop('permission', 0)
        self.children:      CaseInsensitiveDict['Node'] = CaseInsensitiveDict({props['name']: Node(parent=self, **props) for props in kwargs.pop('children', [])})
        self.disabled:      bool = kwargs.pop('disabled', False)

        if self._parent is not None:
            self._parent.children.update({self.name: self})

        if kwargs:
            raise ValueError('Unexpected key-word argument: ' + kwargs.popitem()[0])

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Node):
            return other is self or (self.parent == other.parent and self.name == other.name)
        return False

    def __str__(self) -> str: return f'{(str(self.parent) + "__") if (self.parent is not None and self.parent is not self) else "root:__"}{self.name}'

    @property
    def name(self) -> str: return self._name

    @name.setter
    def name(self, value: str) -> None:
        """Set this node's name to value and update self in parent's children.
        :param value: Node or None to set as parent.
        """
        if self._parent is not None:
            self._parent.children.pop(self.name)
            self._parent.children.update({value: self})
        self._name = value

    @property
    def parent(self) -> 'Node': return self._parent

    @parent.setter
    def parent(self, value: Optional['Node']) -> None:
        """Set this node's parent to value and remove self from old parent's children.
        :param value: Node or None to set as parent.
        """
        if self._parent is not None:
            self._parent.children.pop(self.name)
        if value is not None:
            value.children.update({self.name: self})
        self._parent = value

    def add_children(self, *children: 'Node') -> None:
        """Add children to self.children and set their parent as self.
        :param children: Node to add as child.
        """
        for child in children:
            child.parent = self

    def remove_children(self, *children: Union[str, 'Node']) -> None:
        """Remove children from self.children and set their parent as None.
        :param children: Either name of node or a Node object to search through self for.
        """
        for child in children:
            if child in self.children.values():
                child.parent = None
            elif child in self.children.keys():
                self.children.get(child).parent = None


class CommandSource:
    """Source of command to get data from and send feedback to.

    It is recommended to extend this class so your commands have access to more data about the source.
    """
    __slots__ = ('display_name', 'permission', '_feedback_callback')

    def __init__(self, feedback_callback: Callable[[str, ...], None] = DUMMY_FUNC) -> None:
        self.display_name = ''
        self.permission = 0
        self._feedback_callback = feedback_callback

    def __str__(self) -> str: return self.display_name

    def send_feedback(self, text: str, *args, **kwargs) -> None:
        """Send text, along with any other args and kwargs, to the callback defined during object initialization.
        :param text: text sent through to callback.
        :param args: args to pass to callback.
        :param kwargs: kwargs to pass to callback.
        """
        self._feedback_callback(text, *args, **kwargs)

    def has_permission(self, perm_lvl: int) -> bool:
        """Predicate of if the source can execute a command of a certain permission level.
        :param perm_lvl: Permission level to test
        :return: If {perm_lvl} is at least 0 and not more than self.permission.
        """
        return 0 <= perm_lvl <= self.permission


class CommandContext:
    """Full context for parsing and executing a command from a source."""
    __slots__ = ('_source', '_working_string')

    def __init__(self, working_string: str = '', source: CommandSource = CommandSource()) -> None:
        self._source = source
        self._working_string = working_string

    @property
    def working_string(self) -> str:
        """Original string sent for parsing."""
        return self._working_string

    @property
    def source(self) -> CommandSource:
        """Source that initialized the parse."""
        return self._source
