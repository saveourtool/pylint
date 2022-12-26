# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

from astroid.node_classes import Attribute, Const, Name

from pylint.checkers import BaseChecker
from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker


class SysPathInsertChecker(BaseChecker):
    __implements__ = IAstroidChecker
    name = 'sys-path-insert'
    priority = -1
    SYS_PATH_INSERT = 'no-use-sys-path-insert'
    msgs = {
        'W1805': (
            'Should not use insert(0, ...) to modify sys.path',
            SYS_PATH_INSERT,
            'Use append() instead.'
        ),
    }

    sys_alias = []
    sys_path_alias = []

    def __init__(self, linter=None):
        super(SysPathInsertChecker, self).__init__(linter)

    @check_messages("no-use-sys-path-insert")
    def leave_module(self, node):
        self.sys_alias = []
        self.sys_path_alias = []

    @check_messages("no-use-sys-path-insert")
    def visit_import(self, node):
        for (importname, alias) in node.names:
            if(importname == "sys"):
                self.sys_alias.append(alias if alias else 'sys')

    @check_messages("no-use-sys-path-insert")
    def visit_importfrom(self, node):
        if node.modname != "sys":
            return
        for (importname, alias) in node.names:
            if(importname == "path"):
                self.sys_path_alias.append(alias if alias else 'path')

    def is_sys(self, node):
        return (isinstance(node, Name) and node.name in self.sys_alias)

    def is_sys_path(self, node):
        if isinstance(node, Name) and node.name in self.sys_path_alias:
            return True
        if isinstance(node, Attribute):
            return self.is_sys(node.expr)
        return False

    def is_sys_path_insert(self, node):
        if not isinstance(node, Attribute) or node.attrname != 'insert':
            return False
        return self.is_sys_path(node.expr)

    @check_messages("no-use-sys-path-insert")
    def visit_call(self, node):
        if not self.is_sys_path_insert(node.func):
            return
        if len(node.args) > 0 and isinstance(node.args[0], Const) and node.args[0].value == 0:
            self.add_message(self.SYS_PATH_INSERT, node=node)


def register(linter):
    linter.register_checker(SysPathInsertChecker(linter))
