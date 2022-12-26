# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

from pylint.checkers.huawei.utils.test_case_util import has_not_print_func
from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker
from pylint.checkers import BaseChecker


class TestCaseSysCommandChecker(BaseChecker):
    """Add class member attributes to the class locals dictionary."""

    # This class variable defines the type of checker that we are implementing.
    # In this case, we are implementing an AST checker.
    __implements__ = IAstroidChecker

    # The name defines a custom section of the config for this checker.
    name = "system-func-checker"
    # The priority indicates the order that pylint will run the checkers.
    priority = -1
    # This class variable declares the messages (ie the warnings and errors)
    # that the checker can emit.
    msgs = {
        # Each message has a code, a message that the user will see,
        # a unique symbol that identifies the message,
        # and a detailed help message
        # that will be included in the documentation.
        "W2008": ("TRUST.5.7:Do not use commands related to the operating system platform. Use the cross-platform "
                  "method instead.",
                  "system-func-checker",
                  "TRUST.5.7：禁止使用操作系统平台相关命令行，使用跨平台方法代替")
    }
    # This class variable declares the options
    # that are configurable by the user.
    options = (
        (
            "system-func-do-test-func",
            {
                "default": "testcase",
                "type": "regexp",
            },
        ),
        (
            "system-func",
            {
                "default": "system",
                "type": "regexp",
            },
        ),
    )

    def __init__(self, linter=None):
        super(TestCaseSysCommandChecker, self).__init__(linter)
        self.do_test_func = None
        self.system_func = None

    def open(self):
        super().open()
        if not self.do_test_func:
            self.do_test_func = self.config.system_func_do_test_func
            self.system_func = self.config.system_func

    @check_messages("system-func-checker")
    def visit_module(self, node):
        lines = []
        has_not_print_func(node, self.do_test_func, lines, self.system_func)
        for code_line in lines:
            self.add_message("system-func-checker", line=code_line, node=node)


def register(linter):
    """required method to auto register this checker """
    linter.register_checker(TestCaseSysCommandChecker(linter))
