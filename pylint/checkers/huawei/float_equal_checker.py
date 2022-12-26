# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

import astroid

from pylint.checkers import BaseChecker, utils
from pylint.interfaces import IAstroidChecker


class FloatEqualChecker(BaseChecker):
    __implements__ = IAstroidChecker
    name = 'float-equal'
    priority = -1
    msgs = {
        'W0135': (
            'Do not use == to determine whether floating-point data is equal. '
            'You are advised to use the math.isclose() function.',
            'floating-equal-comparison',
            'Do not use == to determine whether floating-point data is equal. '
            'You are advised to use the math.isclose() function.'
        ),
    }

    def __init__(self, linter=None):
        super(FloatEqualChecker, self).__init__(linter)

    @utils.check_messages("floating-equal-comparison")
    def visit_compare(self, node):
        # NOTE: this checker only works with binary comparisons like 'x == 42'
        # but not 'x == y == 42'
        if len(node.ops) != 1:
            return

        left = node.left
        operator, right = node.ops[0]
        if operator in ("==", "!="):
            self._check_floating_equal_comparison(node, left, right)

    def _check_floating_equal_comparison(self, node, left, right):
        left_type = utils.node_type(left)
        right_type = utils.node_type(right)
        if (
            type(left_type) is not astroid.Const or
            type(right_type) is not astroid.Const
        ):
            return
        if type(left_type.value) is float and type(right_type.value) is float:
            self.add_message("floating-equal-comparison", node=node)


def register(linter):
    linter.register_checker(FloatEqualChecker(linter))
