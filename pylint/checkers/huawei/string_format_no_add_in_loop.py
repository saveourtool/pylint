# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

import astroid

from pylint.checkers import BaseChecker
from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker


class StringFormatNoAddInLoop(BaseChecker):
    __implements__ = IAstroidChecker
    name = 'string-format-no-add-in-loop'
    priority = -1

    msgs = {
        "H1310": (
            "In a loop, the format method,% operator, and join method are used instead of "
            "the '+' and '+=' operators to complete string formatting.",
            "string-format-no-add-in-loop",
            "In a loop, the format method,% operator, and join method are used instead of "
            "the '+' and '+=' operators to complete string formatting.",
        ),
    }

    def __init__(self, linter=None):
        super(StringFormatNoAddInLoop, self).__init__(linter)
        self.loop_range = []
        self.binop_range = []

    @check_messages("string-format-no-add-in-loop")
    def visit_for(self, node):
        self.check_string_add_in_loop(node)

    @check_messages("string-format-no-add-in-loop")
    def visit_while(self, node):
        self.check_string_add_in_loop(node)

    @check_messages("string-format-no-add-in-loop")
    def visit_binop(self, node):
        self.check_binop_in_loop(node)

    @check_messages("string-format-no-add-in-loop")
    def visit_module(self, _):
        self.loop_range = []
        self.binop_range = []

    def check_string_add_in_loop(self, node):
        for node_body in node.body:
            if type(node_body) is astroid.AugAssign:
                if node_body.op == "+=":
                    if type(node_body.value) is astroid.Const and type(node_body.value.value) is str:
                        self.loop_range.append(
                            [node_body.fromlineno, node_body.tolineno])
                        self.add_message(
                            "string-format-no-add-in-loop", node=node_body)
                    elif type(node_body.value) is astroid.BinOp:
                        self.binop_range.append(node_body.lineno)
            if type(node_body) is astroid.Assign:
                if type(node_body.value) is astroid.BinOp:
                    self.loop_range.append(
                        [node_body.fromlineno, node_body.tolineno])

    def check_binop_in_loop(self, node):
        for line_range in self.loop_range:
            if (node.lineno <= line_range[1]) and (node.lineno >= line_range[0]):
                if node.op == "+":
                    if type(node.left) is astroid.Const and type(node.left.value) is str:
                        self.add_message(
                            "string-format-no-add-in-loop", node=node)
                        self.loop_range.remove(line_range)
                    elif type(node.right) is astroid.Const and type(node.right.value) is str:
                        self.add_message(
                            "string-format-no-add-in-loop", node=node)
                        self.loop_range.remove(line_range)
                    else:
                        self.binop_range.append(node.lineno)
        for line_range in self.binop_range:
            if node.lineno == line_range:
                if type(node.left) is astroid.Const and type(node.left.value) is str:
                    self.add_message("string-format-no-add-in-loop", node=node)
                    self.binop_range.remove(line_range)
                elif type(node.right) is astroid.Const and type(node.right.value) is str:
                    self.add_message("string-format-no-add-in-loop", node=node)
                    self.binop_range.remove(line_range)


def register(linter):
    linter.register_checker(StringFormatNoAddInLoop(linter))
