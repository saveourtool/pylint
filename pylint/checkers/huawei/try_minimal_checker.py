# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

import astroid

from pylint.checkers import BaseChecker, utils
from pylint.interfaces import IAstroidChecker


class TryMinimalChecker(BaseChecker):
    __implements__ = IAstroidChecker
    name = 'try-minimal'
    priority = -1
    msgs = {
        "W0719": (
            "The try code block only contains code segments "
            "that may throw exceptions",
            "try-contains-only-one-exception",
            "Avoid putting statements that will not generate exceptions into "
            "the try code block;Avoid putting multiple exception-generating "
            "statements into the same try code block",
        ),
    }

    def __init__(self, linter=None):
        super(TryMinimalChecker, self).__init__(linter)

    def check_try_except(self, node):
        ignoring_number_of_rows = 0
        for statement in node.body:
            if type(statement) is astroid.Return \
                    or type(statement) is astroid.Break \
                    or type(statement) is astroid.Continue:
                ignoring_number_of_rows += 1
        if len(node.body) - ignoring_number_of_rows > 1:
            self.add_message("try-contains-only-one-exception", node=node)

    @utils.check_messages("try-contains-only-one-exception")
    def visit_tryexcept(self, node):
        self.check_try_except(node)


def register(linter):
    linter.register_checker(TryMinimalChecker(linter))
