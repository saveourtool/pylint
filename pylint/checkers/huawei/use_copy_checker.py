# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

import astroid

from pylint.checkers import BaseChecker, utils
from pylint.interfaces import IAstroidChecker


class UseCopyChecker(BaseChecker):
    __implements__ = IAstroidChecker
    name = 'value-assert'
    priority = -1
    msgs = {
        "H0803": ( # python standard 2.1
            "Use copy and deepcopy with caution.",
            "no-use-copy",
            "Use copy and deepcopy with caution.",
        ),
    }

    def __init__(self, linter=None):
        super(UseCopyChecker, self).__init__(linter)

    @utils.check_messages("no-use-copy")
    def visit_call(self, node):
        """Visit a Call node."""
        if type(node.func) is astroid.Attribute:
            if node.func.attrname == "copy" or node.func.attrname == "deepcopy":
                self.add_message("no-use-copy", node=node)


def register(linter):
    linter.register_checker(UseCopyChecker(linter))
