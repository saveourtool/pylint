# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

import astroid

from pylint.checkers import BaseChecker, utils
from pylint.interfaces import IAstroidChecker


class UseAssignmentExpressionChecker(BaseChecker):
    __implements__ = IAstroidChecker
    name = 'value-assert'
    priority = -1
    msgs = {
        "W0137": (
            "Do not use assignment expressions",
            "not-use-assignment-expressions",
            "Emitted when we detect the use of assignment expressions.",
        ),
    }

    def __init__(self, linter=None):
        super(UseAssignmentExpressionChecker, self).__init__(linter)

    @utils.check_messages("not-use-assignment-expressions")
    def visit_namedexpr(self, node):
        self.add_message("not-use-assignment-expressions", node=node)


def register(linter):
    linter.register_checker(UseAssignmentExpressionChecker(linter))
