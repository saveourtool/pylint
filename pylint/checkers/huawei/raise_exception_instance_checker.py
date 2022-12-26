# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

import astroid

from pylint.checkers import BaseChecker
from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker

MSGS = {
        'W0708': (
            'The raise statement must contain an exception instance.',
            'raise-exception-instance',
            'The raise statement must contain an exception instance.'
        ),
    }


class baseSelfChecker(BaseChecker):
    __implements__ = (IAstroidChecker,)

    # configuration section name
    name = "newstyle"
    # messages
    msgs = MSGS
    priority = -2
    # configuration options
    options = ()

    @check_messages("raise-exception-instance")
    def visit_raise(self, node):
        if type(node.parent) is astroid.ExceptHandler or type(node.parent.parent) is astroid.ExceptHandler:
            return
        if hasattr(node, "exc") and node.exc is not None:
            return

        self.add_message("raise-exception-instance", node=node)


def register(linter):
    """required method to auto register this checker """
    linter.register_checker(baseSelfChecker(linter))

