# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

import astroid

from pylint.checkers import BaseChecker
from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker


class ReturnNoneChecker(BaseChecker):
    __implements__ = IAstroidChecker
    name = 'value-assert'
    priority = -1
    msgs = {
        "W0133": (
            "Use an exception to indicate a special case, and do not return None.",
            "not-return-none",
            "Use an exception to indicate a special case, and do not return None.",
        ),
    }

    def __init__(self, linter=None):
        super(ReturnNoneChecker, self).__init__(linter)

    @check_messages("not-return-none")
    def visit_return(self, node):
        if type(node.value) is astroid.Const and node.value.value is None:
            self.add_message("not-return-none", node=node)
        if type(node.value) is astroid.Tuple and type(node.value.elts) is list:
            for i in node.value.elts:
                if type(i) is astroid.Const and i.value is None:
                    self.add_message("not-return-none", node=node)


def register(linter):
    linter.register_checker(ReturnNoneChecker(linter))
