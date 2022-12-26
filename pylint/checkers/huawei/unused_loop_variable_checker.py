# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

import astroid

from pylint.checkers import BaseChecker
from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker


class UnusedLoopVariableChecker(BaseChecker):
    __implements__ = IAstroidChecker
    name = 'unused-loop-variable'
    priority = -1

    msgs = {
        'H3305': (
            "Unused loop variable %s",
            'unused-loop-variable',
            'Use underscore(_) to name redundant variables.'
        ),
    }

    def __init__(self, linter=None):
        super(UnusedLoopVariableChecker, self).__init__(linter)
        self.def_stack = []
        self.use_stack = []

    @check_messages("unused-loop-variable")
    def visit_for(self, node):
        loop_vars = self.get_loop_vars(node.target)
        self.def_stack.append(loop_vars)
        self.use_stack.append(set())

    @check_messages("unused-loop-variable")
    def leave_for(self, node):
        cur_def = self.def_stack.pop(-1)
        cur_used = self.use_stack.pop(-1)
        
        unused = cur_def - cur_used
        left_var = cur_used - cur_def
        if unused:
            msg = list(unused)
            self.add_message('unused-loop-variable',
                             node=node, args=msg, line=node.lineno)
        if left_var and self.use_stack:
            self.use_stack[-1].update(left_var)

    @check_messages("unused-loop-variable")
    def visit_name(self, node):
        self.check_name(node)

    @check_messages("unused-loop-variable")
    def visit_delname(self, node):
        self.check_name(node)

    @check_messages("unused-loop-variable")
    def visit_assignname(self, node):
        # do not check name defined in for-target
        if not self.is_target_name(node):
            self.check_name(node)

    def is_target_name(self, node: astroid.AssignName) -> bool:
        if not self.def_stack or not self.def_stack[-1]:
            return False
        prev_parent = node
        parent_node = node.parent
        while(not isinstance(parent_node, astroid.For)):
            if isinstance(parent_node, astroid.Module):
                return False
            prev_parent = parent_node
            parent_node = parent_node.parent
        return prev_parent is parent_node.target

    def check_name(self, node):
        if not self.def_stack:
            return

        name_str = node.name
        self.use_stack[-1].add(name_str)

    def get_loop_vars(self, node):
        loop_vars = set()
        if isinstance(node, astroid.AssignName) and \
                not node.name.startswith('_'):
            loop_vars.add(node.name)
        if isinstance(node, astroid.Tuple):
            for elt in node.elts:
                if isinstance(elt, astroid.AssignName) and \
                        not elt.name.startswith('_'):
                    loop_vars.add(elt.name)
        return loop_vars


def register(linter):
    linter.register_checker(UnusedLoopVariableChecker(linter))
