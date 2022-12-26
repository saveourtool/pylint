# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

from pylint.checkers import BaseChecker
from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker


class UniqueReturnChecker(BaseChecker):
    __implements__ = IAstroidChecker
    name = 'statement'
    priority = -1
    msgs = {
        'W1801': (
            'The module does not use UTF8 encoding.',
            'not-utf8-encoding',
            'All py should be encodeing by utf8.'
        ),
    }

    def __init__(self, linter=None):
        super(UniqueReturnChecker, self).__init__(linter)

    @check_messages('not-utf8-encoding')
    def visit_module(self, node):
        if node.file_encoding != "utf-8":
            self.add_message(
                'not-utf8-encoding', node=node,
            )


def register(linter):
    linter.register_checker(UniqueReturnChecker(linter))
