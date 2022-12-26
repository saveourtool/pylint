# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

from typing import List, Set

from astroid import nodes

from pylint.checkers import BaseChecker
from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker


class InfiniteLoopChecker(BaseChecker):
    __implements__ = IAstroidChecker
    name = 'infinite-loop'
    priority = -1

    msgs = {
        'H3306': (  # python 3.0 standard 3.3 G.CTL.06
            'Potential infinite loop: %s',
            'infinite-loop',
            'Variable name should be clear and easy-to-read.'
        ),
    }

    potential_breaks = (nodes.Break, nodes.Raise, nodes.Call, nodes.Return)

    def __init__(self, linter=None):
        super(InfiniteLoopChecker, self).__init__(linter)
        self.nested_try_count = 0

    @check_messages("infinite-loop")
    def visit_while(self, node: nodes.While):
        # check whether this is a while-true loop.
        # currently, tautologies (e.g. 0 != 1) are not supported.
        if self.is_while_true(node):
            self.check_while_true(node)

        # if any function call in test condition, skip.
        if next(node.test.nodes_of_class(nodes.Call), False):
            return

        # no function in test; get all names involved in condition.
        loopvar_set = self.get_underlying_names(node.test)
        if not loopvar_set:
            return
        # check any of the loop vars is used.
        bodyvar_set = self.get_underlying_names_in_body(node.body)
        if loopvar_set.intersection(bodyvar_set):
            return

        self.add_message('infinite-loop', node=node,
                         args='loop variant not used in loop body.')

    def check_while_true(self, node: nodes.While):
        for stmt in node.body:
            # if any potential break exists, skip check
            if next(stmt.nodes_of_class(self.potential_breaks), False):
                return
        self.add_message('infinite-loop', node=node,
                         args='while-true loop without break, raise or potential exceptions.')

    def is_while_true(self, node):
        # if this while is wrapped in a try block, skip
        return self.nested_try_count == 0 \
            and isinstance(node.test, nodes.Const) \
            and node.test.value is True

    @check_messages("infinite-loop")
    def visit_tryexcept(self, node: nodes.TryExcept):
        self.nested_try_count += 1

    @check_messages("infinite-loop")
    def leave_tryexcept(self, node: nodes.TryExcept):
        self.nested_try_count -= 1

    def get_underlying_names(self, node: nodes.NodeNG) -> Set[str]:
        return {x.name for x in node.nodes_of_class((nodes.Name, nodes.AssignName))}

    def get_underlying_names_in_body(self, body: List[nodes.NodeNG]):
        for stmt in body:
            yield from (x.name for x in stmt.nodes_of_class((nodes.Name, nodes.AssignName)))


def register(linter):
    linter.register_checker(InfiniteLoopChecker(linter))
