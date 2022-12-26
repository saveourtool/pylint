# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

"""针对规范，优化覆盖面 G.CTL.02 所有的代码都必须是逻辑可达的
"""

import copy

from astroid import nodes

from pylint.checkers import BaseChecker
from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker
from pylint.checkers import utils


class ResizeUnreachableCodeChecker(BaseChecker):
    __implements__ = IAstroidChecker
    name = 'resize-unreachable-code'
    priority = -1

    msgs = {
        'H0302': (
            'the following parts are dead codes',
            'resize-unreachable-code',
            'all code statements need logical accessibility.'
        ),
    }

    def __init__(self, linter=None):
        super().__init__(linter)
        self._tryfinallys = []
        self.linter.stats.reset_node_count()
        self._can_simplify_bool_op = None

    @staticmethod
    def _apply_boolean_simplification_rules(operator, values):
        """Removes irrelevant values or returns shortcircuiting values.

        This function applies the following two rules:
        1) an OR expression with True in it will always be true, and the
           reverse for AND

        2) False values in OR expressions are only relevant if all values are
           false, and the reverse for AND
        """
        simplified_values = []

        for subnode in values:
            inferred_bool = None
            if not next(subnode.nodes_of_class(nodes.Name), False):
                inferred = utils.safe_infer(subnode)
                if inferred:
                    inferred_bool = inferred.bool_value()

            if not isinstance(inferred_bool, bool):
                simplified_values.append(subnode)
            elif (operator == "or") == inferred_bool:
                return [subnode]

        return simplified_values or [nodes.Const(operator == "and")]

    def visit_tryfinally(self, node: nodes.TryFinally) -> None:
        """Update try...finally flag."""
        self._tryfinallys.append(node)

    def leave_tryfinally(self, _: nodes.TryFinally) -> None:
        """Update try...finally flag."""
        self._tryfinallys.pop()

    @check_messages("resize-unreachable-code")
    def visit_return(self, node: nodes.Return) -> None:
        """Return node visitor.

        1 - check if the node has a right sibling (if so, that's some
        unreachable code)
        2 - check if the node is inside the 'finally' clause of a 'try...finally'
        block
        """
        self._check_unreachable(node)
        # Is it inside final body of a try...finally block ?
        self._check_not_in_finally(node, "return", (nodes.FunctionDef,))

    @check_messages("resize-unreachable-code")
    def visit_break(self, node: nodes.Break) -> None:
        """Break node visitor.

        1 - check if the node has a right sibling (if so, that's some
        unreachable code)
        2 - check if the node is inside the 'finally' clause of a 'try...finally'
        block
        """
        # 1 - Is it right sibling ?
        self._check_unreachable(node)
        # 2 - Is it inside final body of a try...finally block ?
        self._check_not_in_finally(node, "break", (nodes.For, nodes.While))

    @check_messages("resize-unreachable-code")
    def visit_continue(self, node: nodes.Continue) -> None:
        """Check is the node has a right sibling (if so, that's some unreachable
        code)
        """
        self._check_unreachable(node)

    @check_messages("resize-unreachable-code")
    def visit_raise(self, node: nodes.Raise) -> None:
        """Check if the node has a right sibling (if so, that's some unreachable
        code)
        """
        self._check_unreachable(node)

    @check_messages("resize-unreachable-code")
    def visit_while(self, node: nodes.While) -> None:
        """Check if the node has a right sibling (if so, that's some unreachable
        code)
        """
        if isinstance(node.test, nodes.Const) and node.test.value is False:
            self.add_message("resize-unreachable-code", node=node)
        if isinstance(node.test, nodes.BoolOp):
            self._check_simplifiable_condition(node.test)

    @check_messages("resize-unreachable-code")
    def visit_if(self, node: nodes.If) -> None:
        """Check if the node has a right sibling (if so, that's some unreachable
        code)
        """
        node_else = node.orelse[0] if node.orelse else None
        if isinstance(node.test, nodes.BoolOp):
            self._check_simplifiable_condition(node.test, node_else)

    def _check_simplifiable_condition(self, node, node_else=None):
        """Check if a boolean condition can be simplified.

        Variables will not be simplified, even in the value can be inferred,
        and expressions like '3 + 4' will remain expanded.
        """
        if not utils.is_test_condition(node):
            return

        self._can_simplify_bool_op = False
        simplified_expr = self._simplify_boolean_operation(node)

        if not self._can_simplify_bool_op:
            return
        if not next(simplified_expr.nodes_of_class(nodes.Name), False):
            if not isinstance(simplified_expr, nodes.Const):
                # todo 需要判段是否小于 真或者假
                ...
            elif simplified_expr.value and node_else:
                self.add_message(
                    "resize-unreachable-code",
                    node=node_else,
                )
            elif not simplified_expr.value:
                self.add_message(
                    "resize-unreachable-code",
                    node=node,
                )

    # 代码出自...\pylint\checkers\refactoring\refactoring_checker.py
    def _simplify_boolean_operation(self, bool_op):
        """Attempts to simplify a boolean operation.

        Recursively applies simplification on the operator terms,
        and keeps track of whether reductions have been made.
        """
        children = list(bool_op.get_children())
        intermediate = [
            self._simplify_boolean_operation(child)
            if isinstance(child, nodes.BoolOp)
            else child
            for child in children
        ]
        result = self._apply_boolean_simplification_rules(bool_op.op, intermediate)
        if len(result) < len(children):
            self._can_simplify_bool_op = True
        if len(result) == 1:
            return result[0]
        simplified_bool_op = copy.copy(bool_op)
        simplified_bool_op.postinit(result)
        return simplified_bool_op

    # 代码出自...\pylint\checkers\refactoring\refactoring_checker.py

    # todo visit_tryexcept 可以处理部分场景诸如赋值语句

    # 代码出自：...\build\lib\pylint\checkers\base\basic_checker.py
    def _check_unreachable(self, node):
        """Check unreachable code."""
        unreach_stmt = node.next_sibling()
        if unreach_stmt is not None:
            if (
                    isinstance(node, nodes.Return)
                    and isinstance(unreach_stmt, nodes.Expr)
                    and isinstance(unreach_stmt.value, nodes.Yield)
            ):
                # Don't add 'unreachable' for empty generators.
                # Only add warning if 'yield' is followed by another node.
                unreach_stmt = unreach_stmt.next_sibling()
                if unreach_stmt is None:
                    return
            self.add_message("resize-unreachable-code", node=unreach_stmt)

    # 代码出自：...\build\lib\pylint\checkers\base\basic_checker.py
    def _check_not_in_finally(self, node, node_name, breaker_classes=()):
        """Check that a node is not inside a 'finally' clause of a
        'try...finally' statement.

        If we find a parent which type is in breaker_classes before
        a 'try...finally' block we skip the whole check.
        """
        # if self._tryfinallys is empty, we're not an in try...finally block
        if not self._tryfinallys:
            return
        # the node could be a grand-grand...-child of the 'try...finally'
        _parent = node.parent
        _node = node
        while _parent and not isinstance(_parent, breaker_classes):
            if hasattr(_parent, "finalbody") and _node in _parent.finalbody:
                self.add_message("lost-exception", node=node, args=node_name)
                return
            _node = _parent
            _parent = _node.parent


def register(linter):
    linter.register_checker(ResizeUnreachableCodeChecker(linter))
