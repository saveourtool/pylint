# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

from pylint.checkers import BaseChecker
from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker

from contextlib import suppress


class HasattrDunderChecker(BaseChecker):
    __implements__ = IAstroidChecker
    name = 'hasattr-dunder'
    priority = -1

    msgs = {
        'H3109': (
            'Should not use hasattr to test object type, use %s instead.',
            'hasattr-dunder',
            'Use built-in method, or isinstance() instead.'
        ),
    }

    dunder_msg_map = {
        '__call__': 'callable(...)',
        '__contains__': 'isinstance(..., Container) (from collections.abc)',
        '__iter__': 'isinstance(..., Iterable) (from collections.abc)',
    }

    def __init__(self, linter=None):
        super(HasattrDunderChecker, self).__init__(linter)

    @check_messages("hasattr-dunder")
    def visit_call(self, node):
        with suppress(AttributeError, IndexError):
            funcname = node.func.name
            argname = node.args[1].value
            if funcname == 'hasattr' and \
                    argname in self.dunder_msg_map:
                self.add_message('hasattr-dunder', node=node,
                                 args=self.dunder_msg_map[argname])


def register(linter):
    linter.register_checker(HasattrDunderChecker(linter))
