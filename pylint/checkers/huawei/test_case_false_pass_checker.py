# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

from pylint.checkers.huawei.utils.test_case_util import check_false_pass
from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker
from pylint.checkers import BaseChecker

class TestCaseFalsePassChecker(BaseChecker):
    """Add class member attributes to the class locals dictionary."""

    # This class variable defines the type of checker that we are implementing.
    # In this case, we are implementing an AST checker.
    __implements__ = IAstroidChecker

    # The name defines a custom section of the config for this checker.
    name = "false-pass-checker"
    # The priority indicates the order that pylint will run the checkers.
    priority = -1
    # This class variable declares the messages (ie the warnings and errors)
    # that the checker can emit.
    msgs = {
        # Each message has a code, a message that the user will see,
        # a unique symbol that identifies the message,
        # and a detailed help message
        # that will be included in the documentation.
        "W2013": ("TRUST.4.3:Forbids false pass test case scripts.",
                  "false-pass-checker",
                  "TRUST.4.3：禁止出现“假通过”的用例脚本")
    }
    # This class variable declares the options
    # that are configurable by the user.
    options = (
        (
            "false-pass-do-test-func",
            {
                "default": "testcase",
                "type": "regexp",
            },
        ),
        (
            "false-pass-asset-func",
            {
                "default": "rt_exit|rt_err",
                "type": "regexp",
            }
        )
    )

    def __init__(self, linter=None):
        super(TestCaseFalsePassChecker, self).__init__(linter)
        self.do_test_funcs = None
        self.assert_funcs = None

    def open(self):
        super().open()
        if not self.do_test_funcs:
            self.do_test_funcs = self.config.false_pass_do_test_func
            self.assert_funcs = self.config.false_pass_asset_func

    @check_messages("false-pass-checker")
    def visit_module(self, node):
        lines = []
        check_false_pass(node, self.do_test_funcs, self.assert_funcs, lines)
        for line in lines:
            self.add_message(
                'false-pass-checker', line=line, node=node
            )

def register(linter):
    """required method to auto register this checker """
    linter.register_checker(TestCaseFalsePassChecker(linter))

