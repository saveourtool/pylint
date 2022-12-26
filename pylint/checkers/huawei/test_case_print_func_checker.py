# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

from pylint.checkers.huawei.utils.test_case_util import has_not_print_func
from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker
from pylint.checkers import BaseChecker


class TestCasePrintFuncChecker(BaseChecker):
    """Add class member attributes to the class locals dictionary."""

    # This class variable defines the type of checker that we are implementing.
    # In this case, we are implementing an AST checker.
    __implements__ = IAstroidChecker

    # The name defines a custom section of the config for this checker.
    name = "print-func-checker"
    # The priority indicates the order that pylint will run the checkers.
    priority = -1
    # This class variable declares the messages (ie the warnings and errors)
    # that the checker can emit.
    msgs = {
        # Each message has a code, a message that the user will see,
        # a unique symbol that identifies the message,
        # and a detailed help message
        # that will be included in the documentation.
        "W2005": ("TRUST.2.9:Locating information cannot be printed only to the console, must be recorded using storage"
                  " media.",
                  "print-func-checker",
                  "TRUST.2.9：不能仅将定位信息打印到控制台，必须使用存储介质记录")
    }
    # This class variable declares the options
    # that are configurable by the user.
    options = (
        (
            "print-func-do-test-func",
            {
                "default": "testcase",
                "type": "regexp",
            },
        ),
        (
            "print-func",
            {
                "default": "print",
                "type": "regexp",
            }
        ),
    )

    def __init__(self, linter=None):
        super(TestCasePrintFuncChecker, self).__init__(linter)
        self.do_test_func = None
        self.print_func = None

    def open(self):
        super().open()
        if not self.do_test_func:
            self.do_test_func = self.config.print_func_do_test_func
            self.print_func = self.config.print_func

    @check_messages("print-func-checker")
    def visit_module(self, node):
        lines = []
        has_not_print_func(node, self.do_test_func, lines, self.print_func)
        for code_line in lines:
            self.add_message("print-func-checker", line=code_line, node=node)


def register(linter):
    """required method to auto register this checker """
    linter.register_checker(TestCasePrintFuncChecker(linter))
