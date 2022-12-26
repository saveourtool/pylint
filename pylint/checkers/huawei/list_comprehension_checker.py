# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

import astroid

from pylint.checkers import BaseChecker
from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker


class ListComprehensionChecker(BaseChecker):
    __implements__ = IAstroidChecker
    name = 'value-assert'
    priority = -1
    msgs = {
        "W0134": (
            "Use generator comprehensive instead of list comprehensive.",
            "not-use-list-comprehension",
            "Use generator comprehensive instead of list comprehensive.",
        ),
    }

    def __init__(self, linter=None):
        super(ListComprehensionChecker, self).__init__(linter)

    @check_messages("not-use-list-comprehension")
    def visit_listcomp(self, node):
        if type(node.parent) == astroid.Call and \
           type(node.parent.func) == astroid.Name and \
           node.parent.func.name == 'len':
            self.add_message("not-use-list-comprehension", node=node)


def register(linter):
    linter.register_checker(ListComprehensionChecker(linter))
