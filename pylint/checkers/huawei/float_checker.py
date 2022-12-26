# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

import astroid

from pylint.checkers import BaseChecker
from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker


class DecimalFloatChecker(BaseChecker):
    __implements__ = IAstroidChecker
    name = 'decimal-float'
    priority = -1
    msgs = {
        'W1117': (
            'In scenarios where precise calculation is required,'
            ' use the decimal module and do not use floating-point numbers' 
            ' to construct the decimal module.',
            'decimal-initialization',
            'In scenarios where precise calculation is required,'
            ' use the decimal module and do not use floating-point numbers' 
            ' to construct the decimal module.'
        ),
    }

    def __init__(self, linter=None):
        super(DecimalFloatChecker, self).__init__(linter)

    @check_messages("decimal-initialization")
    def visit_call(self, node):
        if type(node.func) is astroid.Name:
            if node.func.name == "Decimal":
                for arg in node.args:
                    if type(arg) is astroid.Const and type(arg.value) is float:
                        self.add_message("decimal-initialization", node=node)

        if type(node.func) is astroid.Attribute:
            if (
                type(node.func.expr) is astroid.Name and
                node.func.expr.name == "Decimal" and
                node.func.attrname == "from_float"
            ):
                self.add_message("decimal-initialization", node=node)

    @check_messages("decimal-initialization")
    def visit_binop(self, node):
        if type(node.left) is astroid.Const and type(node.right) is astroid.Const and node.op == "%":
            if type(node.right.value) is float:
                self.add_message("decimal-initialization", node=node)


def register(linter):
    linter.register_checker(DecimalFloatChecker(linter))
