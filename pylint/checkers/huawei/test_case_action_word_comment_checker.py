# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

from pylint.checkers.huawei.utils.test_case_util import get_func_info, check_do_test_func_comment
from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker, ITokenChecker
from pylint.checkers import BaseChecker


class TestCaseActionWordCommentChecker(BaseChecker):
    """Add class member attributes to the class locals dictionary."""

    # This class variable defines the type of checker that we are implementing.
    # In this case, we are implementing an AST checker.
    __implements__ = IAstroidChecker, ITokenChecker

    # The name defines a custom section of the config for this checker.
    name = "aw-func-comment"
    # The priority indicates the order that pylint will run the checkers.
    priority = -1
    # This class variable declares the messages (ie the warnings and errors)
    # that the checker can emit.
    msgs = {
        # Each message has a code, a message that the user will see,
        # a unique symbol that identifies the message,
        # and a detailed help message
        # that will be included in the documentation.
        "W2004": ("TRUST.2.6:Comments for AWs provided for use by use case scripts should be fully standardized.",
                  "aw-func-comment",
                  "TRUST.2.6：提供给用例脚本使用的AW的注释应完整规范")
    }
    # This class variable declares the options
    # that are configurable by the user.
    options = (
        (
            "action-word-func",
            {
                "default": "rt_",
                "type": "regexp",
                "help": (
                    ""
                ),
            }
        ),
    )

    code_lines = []

    def __init__(self, linter=None):
        super(TestCaseActionWordCommentChecker, self).__init__(linter)
        self.action_word_func = None

    def open(self):
        super().open()
        if not self.action_word_func:
            self.action_word_func = self.config.action_word_func

    def process_tokens(self, tokens):
        self.code_lines = tokens

    @check_messages("aw-func-comment")
    def visit_module(self, node):
        func_infos = get_func_info(node)
        for func_info in func_infos:
            if self.action_word_func.match(func_info[0]):
                if check_do_test_func_comment(self.code_lines, func_info):
                    continue
                self.add_message(
                    'aw-func-comment', line=func_info[1]
                )


def register(linter):
    """required method to auto register this checker """
    linter.register_checker(TestCaseActionWordCommentChecker(linter))
