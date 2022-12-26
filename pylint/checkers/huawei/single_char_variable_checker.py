# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

from pylint.checkers import BaseChecker
from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker

bad_names = ["l", "I", "o"]


class SingleCharVariableChecker(BaseChecker):
    __implements__ = IAstroidChecker
    name = 'single-char-variable'
    priority = -1
    BAD_NAME = 'bad-single-char-variable-name'
    msgs = {
        'W1804': (
            'Should not use "l","I" or "o" as variable name',
            BAD_NAME,
            'Variable name should be clear and easy-to-read.'
        ),
    }

    def __init__(self, linter=None):
        super(SingleCharVariableChecker, self).__init__(linter)

    @check_messages("bad-single-char-variable-name")
    def visit_assignname(self, node):
        self.check_assignname(node)

    def check_assignname(self, node):
        if node.name in bad_names:
            self.add_message(self.BAD_NAME, node=node)


def register(linter):
    linter.register_checker(SingleCharVariableChecker(linter))
