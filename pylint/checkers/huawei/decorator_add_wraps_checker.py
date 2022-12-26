# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

import astroid

from pylint.checkers import BaseChecker
from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker


class DecoratorAddWrapsChecker(BaseChecker):
    __implements__ = IAstroidChecker
    name = 'decorator-add-wraps'
    priority = -1

    msgs = {
        'H4004': (  # python 3.0 standard 3.10 G.PSL.04
            'Use functools.wraps to define function decorators',
            'decorator-add-wraps',
            'In the process of writing the decorator, use functools.'
            'wraps to define the function decorator to avoid damage '
            'to the internal properties of the decorated function',
        ),
    }

    def __init__(self, linter=None):
        super(DecoratorAddWrapsChecker, self).__init__(linter)
        self.method_decorators = set()
        self.method = []

    def visit_module(self, node):
        self.method_decorators = set()
        self.method = []

    @check_messages("decorator-add-wraps")
    def visit_functiondef(self, node):
        self.method.append(node)

    @check_messages("decorator-add-wraps")
    def visit_decorators(self, node):
        for decorator in node.nodes:
            if type(decorator) is astroid.Name and \
                    decorator.name not in ["classmethod", "staticmethod"]:
                self.method_decorators.add(decorator.name)
            if type(decorator) is astroid.Call \
                    and type(decorator.func) is astroid.Name:
                self.method_decorators.add(decorator.func.name)

    def _check_decorator(self):
        for decorator in list(self.method_decorators):
            for method in self.method:
                if decorator != method.name:
                    continue
                checked_func_name = None
                funcbody = self.traverse_function(method, checked_func_name)
                if funcbody.decorators is None:
                    self.add_message('decorator-add-wraps',
                                     node=funcbody)
                    continue
                for dec_node in funcbody.decorators.nodes:
                    if type(dec_node) is astroid.Call \
                            and type(dec_node.func) is astroid.Name \
                            and dec_node.func.name != "wraps":
                        self.add_message('decorator-add-wraps',
                                         node=funcbody)
                    elif type(dec_node) is astroid.Call \
                            and type(dec_node.func) is astroid.Attribute \
                            and (dec_node.func.attrname != "wraps" or
                                 dec_node.func.expr.name != "functools"):
                        self.add_message('decorator-add-wraps',
                                         node=funcbody)

    def traverse_function(self, method, checked_func_name):
        for funcbody in method.body:
            if type(funcbody) is astroid.Return and\
                    type(funcbody.value) is astroid.Name:
                checked_func_name = funcbody.value.name
        for funcbody in method.body:
            if type(funcbody) is astroid.FunctionDef and\
                    funcbody.name == checked_func_name:
                return self.traverse_function(funcbody, checked_func_name)
        return method

    @check_messages("decorator-add-wraps")
    def leave_module(self, _):
        self._check_decorator()


def register(linter):
    linter.register_checker(DecoratorAddWrapsChecker(linter))
