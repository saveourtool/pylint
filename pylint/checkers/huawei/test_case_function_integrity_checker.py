# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

from pylint.checkers.huawei.utils.test_case_util import get_func_names, is_test_case
from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker
from pylint.checkers import BaseChecker


class TestCaseFunctionIntegrityCheck(BaseChecker):
    """Add class member attributes to the class locals dictionary."""

    # This class variable defines the type of checker that we are implementing.
    # In this case, we are implementing an AST checker.
    __implements__ = IAstroidChecker

    # The name defines a custom section of the config for this checker.
    name = "function-integrity"
    # The priority indicates the order that pylint will run the checkers.
    priority = -1
    # This class variable declares the messages (ie the warnings and errors)
    # that the checker can emit.
    msgs = {
        # Each message has a code, a message that the user will see,
        # a unique symbol that identifies the message,
        # and a detailed help message
        # that will be included in the documentation.
        "W2000": ("TRUST.2.3:The test case script should organize the test code based on the preset processing, test"
                  + " process, and post-processing.",
                  "function-integrity",
                  "TRUST.2.3：用例脚本应按预置处理、测试过程、后置处理组织测试代码")
    }
    # This class variable declares the options
    # that are configurable by the user.
    options = (
        (
            "pre-func",
            {
                "default": "tc_pre_test",
                "type": "regexp",
                "help": (
                    ""
                ),
            },
        ),
        (
            "do-test-func",
            {
                "default": "testcase",
                "type": "regexp",
                "help": (
                    ""
                ),
            },
        ),
        (
            "clean-test-func",
            {
                "default": "clean_do_test",
                "type": "regexp",
                "help": (
                    ""
                ),
            }
        ),
    )

    def __init__(self, linter=None):
        super(TestCaseFunctionIntegrityCheck, self).__init__(linter)
        self.pre_func = None
        self.do_test_func = None
        self.clean_test_func = None

    def open(self):
        super().open()
        if not self.pre_func:
            self.pre_func = self.config.pre_func
            self.do_test_func = self.config.do_test_func
            self.clean_test_func = self.config.clean_test_func

    @check_messages("function-integrity")
    def visit_module(self, node):
        func_names = get_func_names(node)
        if not is_test_case(func_names, self.pre_func, self.do_test_func, self.clean_test_func):
            return

        fun_list = []
        for func_name in func_names:
            if self.pre_func.match(func_name) and self.pre_func not in fun_list:
                fun_list.append(self.pre_func)
            if self.do_test_func.match(func_name) and self.do_test_func not in fun_list:
                fun_list.append(self.do_test_func)
            if self.clean_test_func.match(func_name) and self.clean_test_func not in fun_list:
                fun_list.append(self.clean_test_func)
            if len(fun_list) == 3:
                return

        self.add_message(
            'function-integrity', node=node
        )


def register(linter):
    """required method to auto register this checker """
    linter.register_checker(TestCaseFunctionIntegrityCheck(linter))

