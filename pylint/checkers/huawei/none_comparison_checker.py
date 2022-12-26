# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

from astroid import nodes

from pylint.checkers import BaseChecker, utils
from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker

class NoneComparisonChecker(BaseChecker):
    __implements__ = IAstroidChecker
    name = 'none-comparison'
    priority = -1
    
    msgs = {
        'H3212': (
            'Comparison %s should be %s',
            'none-comparison',
            'Use is or is not to compare with None. Do not use an equal sign.'
        ),
    }

    def __init__(self, linter=None):
        super().__init__(linter)

    @check_messages("none-comparison")
    def visit_compare(self, node: nodes.Compare) -> None:
        # NOTE: this checker only works with binary comparisons like 'x == 42'
        # but not 'x == y == 42'
        if len(node.ops) != 1:
            return

        left = node.left
        operator, right = node.ops[0]

        if operator in {"==", "!="}:
            self._check_singleton_comparison(left, right, node, operator)

    def _check_singleton_comparison(
        self, left_value, right_value, root_node, operator
    ):
        """Check if == or != is being used to compare a singleton value."""
        none_value = None

        def _is_none_const(node) -> bool:
            return isinstance(node, nodes.Const) and node.value is none_value

        if _is_none_const(left_value) or _is_none_const(right_value):
            singleton_comparison_example = {'==': "'{} is {}'", '!=': "'{} is not {}'"}
            suggestion = singleton_comparison_example[operator].format(
                left_value.as_string(), right_value.as_string()
            )
            self.add_message(
                "none-comparison",
                node=root_node,
                args=(f"'{root_node.as_string()}'", suggestion),
            )


def register(linter):
    linter.register_checker(NoneComparisonChecker(linter))
