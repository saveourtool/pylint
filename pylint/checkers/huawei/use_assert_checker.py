# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

import astroid

from pylint.checkers import BaseChecker, utils
from pylint.interfaces import IAstroidChecker


class UseAssertChecker(BaseChecker):
    __implements__ = IAstroidChecker
    name = 'value-assert'
    priority = -1
    msgs = {
        "W0131": (
            "The assert statement is usually used only in test code. Do not include the assert "
            "function in the production version.",
            "not-use-assert",
            "The assert statement is usually used only in test code. Do not include the assert "
            "function in the production version.",
        ),
    }

    def __init__(self, linter=None):
        super(UseAssertChecker, self).__init__(linter)

    @utils.check_messages("not-use-assert")
    def visit_assert(self, node):
        self.add_message("not-use-assert", node=node)


def register(linter):
    linter.register_checker(UseAssertChecker(linter))
