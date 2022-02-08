###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Tests for the models.py module."""
import sys
import unittest
from pathlib import Path

from dyncommands.models import *
from dyncommands.utils import DUMMY_FUNC

# Boilerplate to allow running script directly.
if __name__ == '__main__' and __package__ is None: sys.path.insert(1, str(Path(__file__).resolve().parent.parent)); __package__ = 'tests'


class TestNode(unittest.TestCase):
    def test_init(self) -> None:
        """Test attribute initialization"""
        parent = Node(name='parent')
        child = Node(parent=parent, name='child', description='child node to parent', permission=100)
        # Parent attrs
        self.assertIsNone(parent.parent)
        self.assertEqual(parent.name, 'parent')
        self.assertEqual(parent.usage, '')
        self.assertEqual(parent.description, '')
        self.assertEqual(parent.permission, 0)
        # Child attrs
        self.assertEqual(child.parent, parent)
        self.assertEqual(child.name, 'child')
        self.assertEqual(child.description, 'child node to parent')
        self.assertEqual(child.permission, 100)
        self.assertEqual(child.children, {})
        self.assertEqual(child.disabled, False)

        self.assertRaises(ValueError, Node, unexpected='unexpected')

    def test_str(self) -> None:
        """__str__ dunder"""
        node = Node()
        self.assertEqual(str(node), 'root:__')

        node.name = 'better-name'
        self.assertEqual(str(node), 'root:__better-name')

        node.add_children(Node(name='child'))
        self.assertEqual(str(node.children['child']), 'root:__better-name__child')

        second = Node(parent=node.children['child'], name='second')
        self.assertEqual(str(second), 'root:__better-name__child__second')

        node.name = 'dif'
        self.assertEqual(str(second), 'root:__dif__child__second')

    def test_children(self) -> None:
        """Children node objects"""
        parent = Node()
        child = Node()
        parent.add_children(child, child, child, child, child)
        self.assertEqual(parent.children, {'': child})

        # Changing name effects the parent
        child.name = 'new'
        self.assertEqual(parent.children, {'new': child})

        # Add second child
        second = Node(name='second')
        parent.add_children(second)
        self.assertEqual(parent.children, {'new': child, 'second': second})

        # Remove children using str
        parent.remove_children('new', 'second')
        self.assertEqual(parent.children, {})

        # Remove children using Node object
        parent.add_children(child, second)
        parent.remove_children(child, second)
        self.assertEqual(parent.children, {})

    def test_recursive_parent(self) -> None:
        """Parent is itself"""
        node = Node()
        node.parent = node
        self.assertIs(node, node.parent)
        self.assertIs(node, node.children[node.name])
        self.assertIs(node.parent, node.children[node.name])


class TestCommandSource(unittest.TestCase):
    def setUp(self) -> None:
        self.source = CommandSource(self.callback)
        self.feedback = ''

    def test_init(self) -> None:
        """Default values of CommandSource"""
        self.assertEqual(self.source.display_name, '')
        self.assertEqual(self.source.permission, 0)
        self.assertIsNot(self.source._feedback_callback, DUMMY_FUNC)

    def test_callback(self) -> None:
        """Test callback feature of CommandSource"""
        self.assertEqual(self.feedback, '')
        self.source.send_feedback('Test')
        self.assertEqual(self.feedback, 'Test')

    def callback(self, *args) -> None:
        self.feedback = args[0]


class TestCommandContext(unittest.TestCase):
    def test_init(self) -> None:
        """Default values of CommandContext"""
        context = CommandContext('working string')
        self.assertEqual(context.working_string, 'working string')
        self.assertEqual(str(context.source), str(CommandSource()))

    def test_properties(self) -> None:
        """Test properties"""
        # No property setters
        self.assertRaises(TypeError, CommandContext.source.fset)
        self.assertRaises(TypeError, CommandContext.working_string.fset)


if __name__ == '__main__':
    unittest.main()
