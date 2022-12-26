# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING
import re

from astroid import nodes

from pylint.checkers.huawei.utils.test_case_util import get_func_expr, get_func_info, check_do_test_func_comment
from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker, ITokenChecker
from pylint.checkers import BaseChecker


class TestCaseProcessFunctionCommentChecker(BaseChecker):
    """Add class member attributes to the class locals dictionary."""

    # This class variable defines the type of checker that we are implementing.
    # In this case, we are implementing an AST checker.
    __implements__ = IAstroidChecker, ITokenChecker

    # The name defines a custom section of the config for this checker.
    name = "do-test-comment"
    # The priority indicates the order that pylint will run the checkers.
    priority = -1
    # This class variable declares the messages (ie the warnings and errors)
    # that the checker can emit.
    msgs = {
        # Each message has a code, a message that the user will see,
        # a unique symbol that identifies the message,
        # and a detailed help message
        # that will be included in the documentation.
        "W2002": ("TRUST.2.4:Use case scripts should make test steps and checkpoints explicit.",
                  "do-test-comment",
                  "TRUST.2.4：用例脚本应将测试步骤和检查点显性化")
    }
    # This class variable declares the options
    # that are configurable by the user.
    options = (
        (
            "do-test-comment-do-test-func",
            {
                "default": "testcase",
                "type": "regexp",
                "help": (
                    ""
                ),
            },
        ),
        (
            "do-test-comment-check-func",
            {
                "default": "CheckPoint",
                "type": "regexp",
                "help": (
                    ""
                ),
            },
        ),
    )

    code_lines = []

    def __init__(self, linter=None):
        super(TestCaseProcessFunctionCommentChecker, self).__init__(linter)
        self.do_test_func = None
        self.check_func = None
        self.has_check_point = False
        self.need_to_check_point = False
        self.enter_test_func = False
        self.comment_in_func = ''
        self.error_line = 0

    def open(self):
        super().open()
        if not self.do_test_func:
            self.do_test_func = self.config.do_test_comment_do_test_func
            if self.config.do_test_comment_check_func == re.compile(''):
                return
            self.check_func = self.config.do_test_comment_check_func

    def process_tokens(self, tokens):
        self.code_lines = tokens

    @check_messages("do-test-comment")
    def visit_module(self, node: nodes.Module):
        func_infos = get_func_info(node)
        for func_info in func_infos:
            if self.do_test_func.match(func_info[0]):
                if check_do_test_func_comment(self.code_lines, func_info):
                    self.has_check_point = True
                else:
                    self.error_line = func_info[1]

        if node.doc_node is None:
            return
        doc_str = node.doc_node.value.lower()
        if any(['步骤' in doc_str, 'step' in doc_str, '测试' in doc_str]) and \
                any(['结果' in doc_str, 'result' in doc_str, '预期' in doc_str]):
            self.has_check_point = True

    def visit_functiondef(self, node: nodes.FunctionDef):
        if not self.do_test_func.match(node.name):
            return
        self.need_to_check_point = True
        self.enter_test_func = True
        if node.doc_node is None:
            return
        doc_str = node.doc_node.value.lower()
        self.comment_in_func += doc_str
        if any(['步骤' in doc_str, 'step' in doc_str, '测试' in doc_str]) and \
                any(['结果' in doc_str, 'result' in doc_str, '预期' in doc_str]):
            self.has_check_point = True

    def leave_functiondef(self, node: nodes.FunctionDef):
        if not self.do_test_func.match(node.name):
            return
        self.enter_test_func = False
        if any(['步骤' in self.comment_in_func, 'step' in self.comment_in_func, '测试' in self.comment_in_func]) and \
                any(['结果' in self.comment_in_func, 'result' in self.comment_in_func, '预期' in self.comment_in_func]):
            self.has_check_point = True
        self.comment_in_func = ''

    def visit_call(self, node: nodes.Call):
        if not self.enter_test_func or self.check_func is None:
            return
        func_name = get_func_expr(node.func)
        if self.check_func.match(func_name):
            self.has_check_point = True

    def visit_expr(self, node: nodes.Expr):
        if not self.enter_test_func:
            return
        if isinstance(node.value, nodes.Const) and isinstance(node.value.value, str):
            self.comment_in_func += node.value.value

    @check_messages("do-test-comment")
    def leave_module(self, node: nodes.Module):
        if self.need_to_check_point:
            if not self.has_check_point:
                self.add_message('do-test-comment', line=self.error_line)
            self.has_check_point = False
            self.need_to_check_point = False


def register(linter):
    """required method to auto register this checker """
    linter.register_checker(TestCaseProcessFunctionCommentChecker(linter))
