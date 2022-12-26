
# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

from pylint.checkers.huawei.utils.test_case_util import has_not_print_func
from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker
from pylint.checkers import BaseChecker


class TestCaseBarredFuncChecker(BaseChecker):
    """Add class member attributes to the class locals dictionary."""

    # This class variable defines the type of checker that we are implementing.
    # In this case, we are implementing an AST checker.
    __implements__ = IAstroidChecker

    # The name defines a custom section of the config for this checker.
    name = "barred-func-checker"
    # The priority indicates the order that pylint will run the checkers.
    priority = -1
    # This class variable declares the messages (ie the warnings and errors)
    # that the checker can emit.
    msgs = {
        # Each message has a code, a message that the user will see,
        # a unique symbol that identifies the message,
        # and a detailed help message
        # that will be included in the documentation.
        "W2010": ("TRUST.5.9:Preferential use of libraries across operating systems platforms.",
                  "barred-func-checker",
                  "TRUST.5.9：优先使用跨操作系统平台的库")
    }
    # This class variable declares the options
    # that are configurable by the user.
    options = (
        (
            "barred-func-do-test-func",
            {
                "default": "testcase",
                "type": "regexp",
            },
        ),
        (
            "barred-func",
            {
                "default": "system",
                "type": "regexp",
            }
        ),
    )

    def __init__(self, linter=None):
        super(TestCaseBarredFuncChecker, self).__init__(linter)
        self.barred_func_do_test_func = None
        self.barred_func = None

    def open(self):
        super().open()
        if not self.barred_func_do_test_func:
            self.barred_func_do_test_func = self.config.barred_func_do_test_func
            self.barred_func = self.config.barred_func

    @check_messages("barred-func-checker")
    def visit_module(self, node):
        lines = []
        has_not_print_func(node, self.barred_func_do_test_func, lines, self.barred_func)
        for code_line in lines:
            self.add_message("barred-func-checker", line=code_line, node=node)


def register(linter):
    """required method to auto register this checker """
    linter.register_checker(TestCaseBarredFuncChecker(linter))
