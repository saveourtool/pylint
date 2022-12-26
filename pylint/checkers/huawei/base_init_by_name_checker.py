# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

import astroid

from pylint.checkers import BaseChecker
from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker


class BaseInitByNameChecker(BaseChecker):
    __implements__ = IAstroidChecker
    name = 'base-init-by-name'
    priority = -1

    msgs = {
        'H3605': (
            '__init__ called by base class name, use super().__init__ instead',
            'base-init-by-name',
            '__init__ called by base class name, use super().__init__ instead'
        ),
    }

    def __init__(self, linter=None):
        super(BaseInitByNameChecker, self).__init__(linter)

    @check_messages("base-init-by-name")
    def visit_functiondef(self, node):
        if node.name != '__init__':
            return
        class_node = self.get_class_node(node)
        if (not class_node) or (not class_node.bases):
            return
        for stmt in node.body:
            initname = self.get_name_init(stmt)
            if initname and self.is_base_class(initname, class_node.bases):
                self.add_message('base-init-by-name', node=stmt)

    def get_class_node(self, node):
        if node is None or isinstance(node, astroid.Module):
            return None
        if isinstance(node, astroid.ClassDef):
            return node
        return self.get_class_node(node.parent) if hasattr(node, 'parent') else None

    def get_name_init(self, node):
        if isinstance(node, astroid.Expr):
            node = node.value
        if isinstance(node, astroid.Call):
            func = node.func
            if isinstance(func, astroid.Attribute) and func.attrname == '__init__':
                return func.expr
        return None

    def is_base_class(self, initname, bases):
        for base in bases:
            if base.as_string() == initname.as_string():
                return True
        return False


def register(linter):
    linter.register_checker(BaseInitByNameChecker(linter))
