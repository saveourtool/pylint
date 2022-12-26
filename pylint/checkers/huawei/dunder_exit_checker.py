# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

import astroid

from pylint.checkers import BaseChecker
from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker


class DunderExitChecker(BaseChecker):
    __implements__ = IAstroidChecker
    name = 'dunder-exit'
    priority = -1

    msgs = {
        'H3712': (
            '__exit__ should return True/False/None or raise another exception',
            'dunder-exit',
            'Variable name should be clear and easy-to-read.'
        ),
    }

    def __init__(self, linter=None):
        super(DunderExitChecker, self).__init__(linter)
        self.is_in_exit = False
        self.exit_args = None

    @check_messages("dunder-exit")
    def visit_functiondef(self, node):
        if not node.name == '__exit__':
            return
        self.is_in_exit = True
        if isinstance(node.args, astroid.Arguments):
            self.exit_args = node.args.args
            if len(self.exit_args) != 4:
                # illegal __exit__, ignore it
                self.exit_args = None
        else:
            self.exit_args = None

    @check_messages("dunder-exit")
    def leave_functiondef(self, node):
        self.is_in_exit = False
        self.exit_args = None

    @check_messages("dunder-exit")
    def visit_return(self, node):
        if not self.is_in_exit or node.value is None:
            # returning implicit None is compliant.
            return

        if isinstance(node.value, astroid.Const):
            return_value = node.value.value
            for compliant_value in [True, False, None]:
                # we cannot use if return_value in [T, F, N] as python would use == to compare,
                # resulting in False negative on 0 and 1.
                if return_value is compliant_value:
                    return
            # is a constant value, but not [True, False, None]
            self.add_message("dunder-exit", node=node)
        # non-const return value, compliant.
        return

    @check_messages("dunder-exit")
    def visit_raise(self, node):
        if (not self.is_in_exit) or (not self.exit_args):
            return
        exc_type_argname = self.get_arg_name(self.exit_args[1])
        exc_value_argname = self.get_arg_name(self.exit_args[2])
        if (not exc_type_argname) or (not exc_value_argname):
            return

        if isinstance(node.exc, astroid.Call):
            func = node.exc.func
            arg = node.exc.args
            if self.get_call_func_name(func) == exc_type_argname and \
                    self.get_call_arg_name(arg) == exc_value_argname:
                self.add_message("dunder-exit", node=node)
        # not a re-raise, compliant.
        return

    def get_arg_name(self, node):
        if isinstance(node, astroid.AssignName):
            return node.name
        return None

    def get_call_func_name(self, func):
        if isinstance(func, astroid.Name):
            return func.name
        return None

    def get_call_arg_name(self, arg):
        if isinstance(arg, list) and len(arg) == 1 and \
                isinstance(arg[0], astroid.Name):
            return arg[0].name
        return None


def register(linter):
    linter.register_checker(DunderExitChecker(linter))
