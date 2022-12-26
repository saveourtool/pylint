# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

import re

from astroid import nodes

from pylint.checkers.huawei.utils.test_case_util import get_func_from_config
from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker
from pylint.checkers import BaseChecker

class TestCaseHardCodedChecker(BaseChecker):
    """Add class member attributes to the class locals dictionary."""

    # This class variable defines the type of checker that we are implementing.
    # In this case, we are implementing an AST checker.
    __implements__ = IAstroidChecker

    # The name defines a custom section of the config for this checker.
    name = "hard-code-check"
    # The priority indicates the order that pylint will run the checkers.
    priority = -1
    # This class variable declares the messages (ie the warnings and errors)
    # that the checker can emit.
    msgs = {
        # Each message has a code, a message that the user will see,
        # a unique symbol that identifies the message,
        # and a detailed help message
        # that will be included in the documentation.
        "W2007": ("TRUST.5.1:Do not hardcode test data that may change in test case scripts.",
                  "hard-code-check",
                  "TRUST.5.1：用例脚本中禁止对可能变化的测试数据硬编码")
    }
    # This class variable declares the options
    # that are configurable by the user.
    options = (
        (
            "hard-code-do-test-func",
            {
                "default": "testcase",
                "type": "regexp",
            },
        ),
    )

    code_lines = []

    def __init__(self, linter=None):
        super(TestCaseHardCodedChecker, self).__init__(linter)
        self.do_test_funcs = None
        self.enter_checked_func = False
        self.ip_pattern = re.compile(
            r'^((2'                     # 若第一位为2
            r'(5[0-5]|'                 # 若第二位为5,则第三位为 0-5
            r'[0-4]\d))|'               # 若第二位为0-4,则第三位为 0-9
            r'[0-1]?\d{1,2})'           # 若第一位为 0-1或只有一到两位数，则剩下两位为0-99
            r'(\.((2(5[0-5]|[0-4]\d))|[0-1]?\d{1,2})){3}$')   # 和以上一样，前面多了'.', 重复3次

    def open(self):
        super().open()
        if not self.do_test_funcs:
            self.do_test_funcs = self.config.hard_code_do_test_func

    def visit_functiondef(self, node: nodes.FunctionDef):
        if self.do_test_funcs.match(node.name):
            self.enter_checked_func = True

    def leave_functiondef(self, node: nodes.FunctionDef):
        if not self.do_test_funcs:
            return

        if self.do_test_funcs.match(node.name):
            self.enter_checked_func = False

    @check_messages("hard-code-check")
    def visit_const(self, node: nodes.Const):
        if not self.enter_checked_func:
            return
        if not isinstance(node.value, str):
            return
        if isinstance(node.parent, nodes.Expr) and isinstance(node.parent.value, nodes.Const):
            return

        if self.ip_pattern.match(node.value):
            self.add_message('hard-code-check', node=node)


def register(linter):
    """required method to auto register this checker """
    linter.register_checker(TestCaseHardCodedChecker(linter))
