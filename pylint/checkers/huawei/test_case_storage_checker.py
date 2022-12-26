# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

from astroid import nodes

from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker
from pylint.checkers import BaseChecker


class TestCaseStorageChecker(BaseChecker):
    """Add class member attributes to the class locals dictionary."""

    # This class variable defines the type of checker that we are implementing.
    # In this case, we are implementing an AST checker.
    __implements__ = IAstroidChecker

    # The name defines a custom section of the config for this checker.
    name = "storage-media-check"
    # The priority indicates the order that pylint will run the checkers.
    priority = -1
    # This class variable declares the messages (ie the warnings and errors)
    # that the checker can emit.
    msgs = {
        # Each message has a code, a message that the user will see,
        # a unique symbol that identifies the message,
        # and a detailed help message
        # that will be included in the documentation.
        "W2009": ("TRUST.5.8:Do not use storage media specific to the operating system to store information.",
                  "storage-media-check",
                  "TRUST.5.8：禁止使用操作系统特有的存储介质来存储信息")
    }
    # This class variable declares the options
    # that are configurable by the user.
    options = (
        (
            "storage-media-do-test-func",
            {
                "default": "testcase",
                "type": "regexp",
            },
        ),
    )

    code_lines = []

    def __init__(self, linter=None):
        super(TestCaseStorageChecker, self).__init__(linter)
        self.do_test_funcs = None

    def open(self):
        super().open()
        if not self.do_test_funcs:
            self.do_test_funcs = self.config.storage_media_do_test_func

    def process_tokens(self, tokens):
        self.code_lines = tokens

    @check_messages("storage-media-check")
    def visit_const(self, node: nodes.Const):
        if not isinstance(node.value, str):
            return
        if isinstance(node.parent, nodes.Expr) and isinstance(node.parent.value, nodes.Const):
            return
        if node.value.endswith('.xlsx') or node.value.endswith('.xls'):
            self.add_message("storage-media-check", node=node)


def register(linter):
    """required method to auto register this checker """
    linter.register_checker(TestCaseStorageChecker(linter))
