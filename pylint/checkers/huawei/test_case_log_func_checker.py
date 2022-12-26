# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

from astroid import nodes

from pylint.checkers.huawei.utils.test_case_util import get_func_expr
from pylint.interfaces import IAstroidChecker
from pylint.checkers import BaseChecker, utils


class TestCaseLogFuncChecker(BaseChecker):
    """Add class member attributes to the class locals dictionary."""

    # This class variable defines the type of checker that we are implementing.
    # In this case, we are implementing an AST checker.
    __implements__ = IAstroidChecker

    # The name defines a custom section of the config for this checker.
    name = "log-func-checker"
    # The priority indicates the order that pylint will run the checkers.
    priority = -1
    # This class variable declares the messages (ie the warnings and errors)
    # that the checker can emit.
    msgs = {
        # Each message has a code, a message that the user will see,
        # a unique symbol that identifies the message,
        # and a detailed help message
        # that will be included in the documentation.
        "W2006": ("TRUST.2.10:Logs should be graded and used correctly.",
                  "log-func-checker",
                  "TRUST.2.10：应对日志进行分级并正确使用")
    }
    # This class variable declares the options
    # that are configurable by the user.
    options = (
        (
            "log-do-test-func",
            {
                "default": "testcase",
                "type": "regexp",
            },
        ),
        (
            "log-func",
            {
                "default": "logging\.info",
                "type": "regexp",
            }
        ),
    )

    def __init__(self, linter=None):
        super(TestCaseLogFuncChecker, self).__init__(linter)
        self.enter_checked_func = False
        self.except_nest = 0
        self.do_test_funcs = None
        self.log_funcs = None
        self.log_info_funcs = None

    def open(self):
        super().open()
        if not self.do_test_funcs:
            self.do_test_funcs = self.config.log_do_test_func
            self.log_funcs = self.config.log_func

    def visit_functiondef(self, node: nodes.FunctionDef):
        if self.do_test_funcs.match(node.name):
            self.enter_checked_func = True

    def leave_functiondef(self, node: nodes.FunctionDef):
        if not self.do_test_funcs:
            return
        if self.do_test_funcs.match(node.name):
            self.enter_checked_func = False

    def visit_excepthandler(self, node: nodes.ExceptHandler):
        if self.enter_checked_func:
            self.except_nest += 1

    def leave_excepthandler(self, node: nodes.ExceptHandler):
        if self.enter_checked_func:
            self.except_nest -= 1

    @utils.check_messages("log-func-checker")
    def visit_call(self, node: nodes.Call):
        if self.except_nest > 0:
            func_expr = get_func_expr(node.func)
            if self.log_funcs.match(func_expr):
                self.add_message('log-func-checker', node=node)


def register(linter):
    linter.register_checker(TestCaseLogFuncChecker(linter))
