# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

import re

from pylint.checkers.huawei.utils.test_case_util import has_asset_func
from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker
from pylint.checkers import BaseChecker

class TestCaseAssetCallCheck(BaseChecker):
    """Add class member attributes to the class locals dictionary."""

    # This class variable defines the type of checker that we are implementing.
    # In this case, we are implementing an AST checker.
    __implements__ = IAstroidChecker

    # The name defines a custom section of the config for this checker.
    name = "asset-call-checker"
    # The priority indicates the order that pylint will run the checkers.
    priority = -1
    # This class variable declares the messages (ie the warnings and errors)
    # that the checker can emit.
    msgs = {
        # Each message has a code, a message that the user will see,
        # a unique symbol that identifies the message,
        # and a detailed help message
        # that will be included in the documentation.
        "W2003": ("TRUST.2.5:Assertion method using the test code framework built-in.",
                  "asset-call-checker",
                  "TRUST.2.5：使用测试代码框架built-in的断言方法")
    }
    # This class variable declares the options
    # that are configurable by the user.
    options = (
        (
            "asset-do-test-func",
            {
                "default": "testcase",
                "type": "regexp",
            },
        ),
        (
            "asset-func",
            {
                "default": "rt_exit",
                "type": "regexp",
            }
        ),
    )

    def __init__(self, linter=None):
        super(TestCaseAssetCallCheck, self).__init__(linter)
        self.do_test_funcs = None
        self.assert_funcs = None

    def open(self):
        super().open()
        if not self.do_test_funcs:
            self.do_test_funcs = self.config.asset_do_test_func
            if self.config.asset_func == re.compile(''):
                return
            self.assert_funcs = self.config.asset_func

    @check_messages("asset-call-checker")
    def visit_module(self, node):
        if self.assert_funcs is None:
            return
        lines = []
        has_asset_func(node, self.do_test_funcs, self.assert_funcs, lines)
        for line in lines:
            self.add_message(
                'asset-call-checker', line=line, node=node
            )

def register(linter):
    """required method to auto register this checker """
    linter.register_checker(TestCaseAssetCallCheck(linter))
