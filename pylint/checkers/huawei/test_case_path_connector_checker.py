# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING
import re

from astroid import nodes

from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker
from pylint.checkers import BaseChecker
from pylint.checkers.huawei.utils.test_case_util import get_func_expr


class TestCasePathConnectorChecker(BaseChecker):
    """Add class member attributes to the class locals dictionary."""

    # This class variable defines the type of checker that we are implementing.
    # In this case, we are implementing an AST checker.
    __implements__ = IAstroidChecker

    # The name defines a custom section of the config for this checker.
    name = "path-connect-checker"
    # The priority indicates the order that pylint will run the checkers.
    priority = -1
    # This class variable declares the messages (ie the warnings and errors)
    # that the checker can emit.
    msgs = {
        # Each message has a code, a message that the user will see,
        # a unique symbol that identifies the message,
        # and a detailed help message
        # that will be included in the documentation.
        "W2012": ("TRUST.5.11:Use the standard library to combine file paths. Do not use character string "
                  "concatenation or explicit path separators (/),\\).",
                  "path-connect-checker",
                  "TRUST.5.11：使用标准库拼接文件路径，禁止直接使用字符串拼接和显式使用 ‘/’,’\\’路径分隔符")
    }
    # This class variable declares the options
    # that are configurable by the user.
    options = (
        (
            "path-connect-do-test-func",
            {
                "default": "testcase",
                "type": "regexp",
            },
        ),
    )

    def __init__(self, linter=None):
        super(TestCasePathConnectorChecker, self).__init__(linter)
        self.enter_checked_func = False
        self.do_test_funcs = None
        self.path_pattern = re.compile('^[0-9a-zA-Z._\\- \u4e00-\u9fa5]*$')

    def open(self):
        super().open()
        if not self.do_test_funcs:
            self.do_test_funcs = self.config.path_connect_do_test_func

    def visit_functiondef(self, node: nodes.FunctionDef):
        if self.do_test_funcs.match(node.name):
            self.enter_checked_func = True

    def leave_functiondef(self, node: nodes.FunctionDef):
        if not self.do_test_funcs:
            return
        if self.do_test_funcs.match(node.name):
            self.enter_checked_func = False

    @check_messages("path-connect-checker")
    def visit_const(self, node: nodes.Const):
        """
        判断 '+' 操作中字符串是否包含'\' 或 '/'
        """
        if not self.enter_checked_func:
            return
        if not isinstance(node.value, str):
            return
        if isinstance(node.parent, nodes.Expr) and isinstance(node.parent.value, nodes.Const):
            return

        if isinstance(node.value, str):
            if not (isinstance(node.parent, nodes.BinOp) and node.parent.op == '+'):
                return
            if '\\' in node.value:
                value_list = node.value.split('\\')
            elif '/' in node.value:
                value_list = node.value.split('/')
            else:
                return
            for value in value_list:
                if not self.path_pattern.match(value):
                    return
            self.add_message("path-connect-checker", node=node)

    @check_messages("path-connect-checker")
    def visit_call(self, node: nodes.Call):
        """
        判断os.path.join字符串参数是否含有’\\‘ 或 ’/‘
        """
        if not self.enter_checked_func:
            return
        func_expr = get_func_expr(node.func)
        if func_expr != 'os.path.join':
            return
        for arg in node.args:
            if isinstance(arg, nodes.Const):
                if isinstance(arg.value, str) and '\\' in arg.value or '/' in arg.value:
                    self.add_message("path-connect-checker", node=arg)


def register(linter):
    """required method to auto register this checker """
    linter.register_checker(TestCasePathConnectorChecker(linter))
