# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

import astroid
from astroid import nodes

from pylint.checkers import BaseChecker
from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker


class AddStaticClassMethodDecoratorChecker(BaseChecker):
    __implements__ = IAstroidChecker
    name = 'add-static-class-method-decorator'
    priority = -1

    msgs = {
        'H3607': (
            'add staticmethod or classmethod decorator when a method of a class does not need to access an instance.',
            'add-staticmethod-or-classmethod-decorator',
            'add staticmethod or classmethod decorator when a method of a class does not need to access an instance.'
        ),
    }

    def __init__(self, linter=None):
        super(AddStaticClassMethodDecoratorChecker, self).__init__(linter)
        self.arg_in_func_body = []
        
    @staticmethod
    def is_abstractmethod(func):
        '''
            whether method is abstract method or not
        '''
        if func.decorators is not None:
            for func_decorators in func.decorators.nodes:
                if func_decorators.as_string() in ["abc.abstractmethod", "abstractmethod"]:
                    return True
        return False

    @check_messages("add-static-class-method-decorator")
    def visit_classdef(self, node):
        if not node.bases:
            self._check_add_staticmethod_or_classmethod(node)

    def _check_add_staticmethod_or_classmethod(self, node):
        for funcbody in node.body:
            if type(funcbody) is astroid.FunctionDef:
                if funcbody.decorators is not None:
                    for func_decorators in funcbody.decorators.nodes:
                        if type(func_decorators) is astroid.Name and func_decorators.name in ["classmethod",
                                                                                              "staticmethod"]:
                            break
                    continue
                if funcbody.name == "__init__":
                    continue
                if len(funcbody.args.args) == 0:
                    continue
                # skip a abstract method
                if self.is_abstractmethod(funcbody):
                    continue
                if len(funcbody.body) > 0 and type(funcbody.body[0]) is astroid.Pass:
                    continue
                else:
                    self.arg_in_func_body.append(funcbody)

    def visit_name(self, name):
        line_no = int(name.lineno)
        for funcbody in self.arg_in_func_body:
            arg_name = funcbody.args.args[0].name
            fromline = int(funcbody.fromlineno)
            toline = int(funcbody.tolineno)
            if (line_no >= fromline) and (line_no <= toline):
                if name.name == arg_name:
                    self.arg_in_func_body.remove(funcbody)
                break

    def leave_module(self, _):
        for node in self.arg_in_func_body:
            self.add_message(
                "add-staticmethod-or-classmethod-decorator", node=node)
        self.arg_in_func_body = []


def register(linter):
    linter.register_checker(AddStaticClassMethodDecoratorChecker(linter))
