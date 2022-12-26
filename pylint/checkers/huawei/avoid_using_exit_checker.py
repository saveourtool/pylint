# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

import astroid
from astroid import nodes

import pylint.checkers.huawei.utils.util as huawei_util
from pylint.checkers import BaseChecker
from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker


class AvoidUsingExitChecker(BaseChecker):
    __implements__ = IAstroidChecker
    name = 'avoid-using-exit'
    priority = -1

    msgs = {
        'H3711': (
            'Avoid calling sys.exit() and raise SystemExit() in the function',
            'avoid-using-exit',
            'Calling sys.exit() in a function will cause a lot of trouble '
            'to the caller, and this kind of design should be avoided',
        ),
    }

    def __init__(self, linter=None):
        super(AvoidUsingExitChecker, self).__init__(linter)
        self.main_begin = 0
        self.main_end = 0
        # called function list in main statement
        self.calls = []

    @check_messages("avoid-using-exit")
    def visit_module(self, node):
        self.main_begin = 0
        self.main_end = 0
        for body in node.body:
            if huawei_util.check_if_main(body):
                self.main_begin = body.fromlineno
                self.main_end = body.tolineno
                self.walk_main_statement(body)
                break

    @staticmethod
    def _check_avoid_using_exit(name):
        if name == "exit" or name == "SystemExit":
            return True
        
    @classmethod    
    def get_function_name(cls, node):
        if node is None or isinstance(node, nodes.Module):
            return None
        if isinstance(node, nodes.FunctionDef):
            if isinstance(node.parent, nodes.ClassDef):
                return node.parent.name + "." + node.name
            else:
                return node.name
        return cls.get_function_name(node.parent)

    @check_messages("avoid-using-exit")
    def visit_attribute(self, node):
        if type(node.expr) is astroid.Name \
                and node.expr.name == "sys" \
                and self._check_avoid_using_exit(node.attrname):
            if node.lineno > self.main_end \
                    or node.lineno < self.main_begin:
                self.pop_error_message(node=node)

    @check_messages("avoid-using-exit")
    def visit_name(self, name):
        if self._check_avoid_using_exit(name.name):
            if name.lineno > self.main_end or name.lineno < self.main_begin:
                self.pop_error_message(node=name)
                
    def pop_error_message(self, node):
        # if function is called in main statement, not pop error message
        if self.get_function_name(node) not in self.calls:
            self.add_message('avoid-using-exit', node=node)
        
    def check_main_call(self, node):
        if not isinstance(node, nodes.Call):
            return
        # call function
        if isinstance(node.func, nodes.Name):
            self.calls.append(node.func.as_string())
        # call class method
        elif isinstance(node.func, nodes.Attribute):
            func_str = node.func.as_string()
            if not isinstance(node.func.expr, nodes.Name):
                return
            try:
                for var_type in node.func.expr.infer():
                    # object method
                    if isinstance(var_type, astroid.bases.Instance):
                        pytype = var_type.pytype()
                        self.calls.append(pytype.split('.')[1] + "." + func_str.split('.')[1])
                    # classmethod or staticmethod
                    elif isinstance(var_type, nodes.ClassDef):
                        self.calls.append(var_type.name + "." + func_str.split('.')[1])
            except astroid.InferenceError:
                return

    def walk_main_statement(self, parent):
        for child in parent.get_children():
            self.check_main_call(child)
            self.walk_main_statement(child)

def register(linter):
    linter.register_checker(AvoidUsingExitChecker(linter))
