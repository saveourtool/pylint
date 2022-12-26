# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

import re

import astroid

from pylint.checkers import BaseChecker
from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker


class UseSystemPathChecker(BaseChecker):
    __implements__ = IAstroidChecker
    name = 'use-system-path'
    priority = -1

    msgs = {
        "W1311": (
            "Use methods in the os.path library instead of string concatenation "
            "to complete file system path operations.",
            "use-system-path",
            "Use methods in the os.path library instead of string concatenation "
            "to complete file system path operations.",
        ),
    }

    regex_length_threshold = 1000

    def __init__(self, linter=None):
        super(UseSystemPathChecker, self).__init__(linter)

    def check_os_path_attribute(self, node):
        if type(node.parent) is astroid.Call \
                and type(node.parent.func) is astroid.Attribute \
                and type(node.parent.func.expr) is astroid.Attribute \
                and node.parent.func.expr.attrname == "path" \
                and type(node.parent.func.expr.expr) is astroid.Name \
                and node.parent.func.expr.expr.name == "os":
            return
        self.add_message("use-system-path", node=node)

    def check_binop_string_path(self, node):
        if node.op == "+":
            path_value = ""
            if type(node.left) is astroid.Const \
                    and type(node.left.value) is str:
                path_value = node.left.value
            elif type(node.right) is astroid.Const \
                    and type(node.right.value) is str:
                path_value = node.right.value
            if len(path_value) < self.regex_length_threshold \
                    and re.match(r'(?:[A-Z]:|\\|\/|(?:[\~\.]{1,2}[\/\\])+)[\w+\\\s_\-\(\)\/]+', path_value):
                self.check_os_path_attribute(node)

    @check_messages("use-system-path")
    def visit_binop(self, node):
        self.check_binop_string_path(node)


def register(linter):
    linter.register_checker(UseSystemPathChecker(linter))
