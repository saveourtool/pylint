# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

import re

from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker
from pylint.checkers import BaseChecker
from astroid import nodes


class TestCaseAbsolutePathChecker(BaseChecker):
    """Add class member attributes to the class locals dictionary."""

    # This class variable defines the type of checker that we are implementing.
    # In this case, we are implementing an AST checker.
    __implements__ = IAstroidChecker

    # The name defines a custom section of the config for this checker.
    name = "absolute-path-checker"
    # The priority indicates the order that pylint will run the checkers.
    priority = -1
    # This class variable declares the messages (ie the warnings and errors)
    # that the checker can emit.
    msgs = {
        # Each message has a code, a message that the user will see,
        # a unique symbol that identifies the message,
        # and a detailed help message
        # that will be included in the documentation.
        "W2011": ("TRUST.5.10:Do not use absolute paths directly.",
                  "absolute-path-checker",
                  "TRUST.5.10：禁止直接使用绝对路径")
    }
    # This class variable declares the options
    # that are configurable by the user.
    options = (
        (
            "absolute-path-do-test-func",
            {
                "default": "^testcase$",
                "type": "regexp",
            },
        ),
        (
            "absolute-path-filter",
            {
                "default": "",
                "type": "regexp",
            }
        )
    )

    def __init__(self, linter=None):
        super(TestCaseAbsolutePathChecker, self).__init__(linter)
        self.do_test_funcs = None
        self.enter_checked_func = False
        self.path_pattern = re.compile('^[0-9a-zA-Z\._\\- \u4e00-\u9fa5]*$')
        self.begin_pattern = re.compile('^[a-zA-Z]:$')
        self.path_filter_pattern = None

    def open(self):
        super().open()
        if not self.do_test_funcs:
            self.do_test_funcs = self.config.absolute_path_do_test_func
            if self.config.absolute_path_filter != re.compile(''):
                self.path_filter_pattern = self.config.absolute_path_filter

    def visit_functiondef(self, node: nodes.FunctionDef):
        if self.do_test_funcs.match(node.name):
            self.enter_checked_func = True

    def leave_functiondef(self, node: nodes.FunctionDef):
        if not self.do_test_funcs:
            return
        if self.do_test_funcs.match(node.name):
            self.enter_checked_func = False

    @check_messages("absolute-path-checker")
    def visit_const(self, node: nodes.Const):
        """
        检查常量是否符合绝对路径形式
        """
        if not self.enter_checked_func:
            return
        if not isinstance(node.value, str):
            return
        if isinstance(node.parent, nodes.Expr) and isinstance(node.parent.value, nodes.Const):
            return
        if self.path_filter_pattern and self.path_filter_pattern.match(node.value):
            return

        if '/' in node.value:
            value_list = node.value.split('/')
            if value_list[0] != '' and not self.begin_pattern.match(value_list[0]):
                return
        elif '\\' in node.value:
            value_list = node.value.split('\\')
            if not self.begin_pattern.match(value_list[0]):
                return
        else:
            return

        is_absolute_path = False
        for value in value_list[1:]:
            if value != '':
                is_absolute_path = True
                if not self.path_pattern.match(value):
                    return

        if is_absolute_path:
            self.add_message("absolute-path-checker", node=node)


def register(linter):
    """required method to auto register this checker """
    linter.register_checker(TestCaseAbsolutePathChecker(linter))
