# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

from pylint.checkers.utils import check_messages
from pylint.checkers.huawei.utils.test_case_util import get_func_names, is_test_case
from pylint.interfaces import IAstroidChecker
from pylint.checkers import BaseChecker


class TestCasePostProcessingFunctionCheck(BaseChecker):
    """Add class member attributes to the class locals dictionary."""

    # This class variable defines the type of checker that we are implementing.
    # In this case, we are implementing an AST checker.
    __implements__ = IAstroidChecker

    # The name defines a custom section of the config for this checker.
    name = "post-processing"
    # The priority indicates the order that pylint will run the checkers.
    priority = -1
    # This class variable declares the messages (ie the warnings and errors)
    # that the checker can emit.
    msgs = {
        # Each message has a code, a message that the user will see,
        # a unique symbol that identifies the message,
        # and a detailed help message
        # that will be included in the documentation.
        "W2001": (
            "TRUST.1.2:Perform the post-processing steps no matter whether the test case script fails to be executed"
            + " or an exception occurs.",
            "post-processing",
            "TRUST.1.2：无论用例脚本执行失败或出现异常，都必须执行后置处理步骤"
        )
    }
    # This class variable declares the options
    # that are configurable by the user.
    options = (
        (
            "post-processing-pre-func",
            {
                "default": "tc_pre_test",
                "type": "regexp",
                "help": (
                    ""
                ),
            },
        ),
        (
            "post-processing-do-test-func",
            {
                "default": "testcase",
                "type": "regexp",
                "help": (
                    ""
                ),
            },
        ),
        (
            "post-processing-clean-test-func",
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
        super(TestCasePostProcessingFunctionCheck, self).__init__(linter)
        self.pre_func = None
        self.do_test_func = None
        self.clean_test_func = None

    def open(self):
        super().open()
        if not self.pre_func:
            self.pre_func = self.config.post_processing_pre_func
            self.do_test_func = self.config.post_processing_do_test_func
            self.clean_test_func = self.config.post_processing_clean_test_func

    @check_messages("post-processing")
    def visit_module(self, node):
        func_names = get_func_names(node)
        if not is_test_case(
                func_names,
                self.pre_func,
                self.do_test_func,
                self.clean_test_func):
            return

        for func_name in func_names:
            if self.clean_test_func.match(func_name):
                return

        self.add_message(
            'post-processing', node=node
        )


def register(linter):
    """required method to auto register this checker """
    linter.register_checker(TestCasePostProcessingFunctionCheck(linter))
