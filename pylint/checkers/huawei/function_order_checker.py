# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

import astroid

from pylint.checkers import BaseChecker
from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker


class FunctionOrderChecker(BaseChecker):
    __implements__ = IAstroidChecker
    name = 'function-order'
    priority = -1
    
    msgs = {
        'H3606': (
            '%s.%s should be after %s.%s',
            'function-order',
            'Class methods should be defined in line order.'
        ),
    }

    WEIGHT_INFO = {
        '__new__': 0,
        '__init__': 1,
        '__post_init__': 2,
        'magic_method': 3,
        'property': 4,
        'staticmethod': 5,
        'classmethod': 6,
        'method': 7,
        'private_method': 8,
    }

    def __init__(self, linter=None):
        super().__init__(linter)
        self.errors = {}

    @staticmethod
    def check_decorators(func_node):
        '''
            Processing methods with staticmethod, classmethod, and property decorators
            Other Decorators as Common Methods
        '''
        decorators = func_node.decorators
        if decorators is None:
            return None
        for decorator in decorators.nodes:
            if isinstance(decorator, astroid.Name) and decorator.name in ('staticmethod' , \
                                                                    'classmethod', 'property'):
                return decorator.name
        return 'method'

    @check_messages("function-order")
    def visit_classdef(self, node):
        '''
            Check whether the function definition sequence complies with the rules and collect alarm information.
            Then output the alarm information.
            Clear alarm information to prevent repeated output.
        '''
        self.check_function_order(node)
        self.pop_errors()
        self.errors.clear()

    def check_function_order(self, node):
        '''
            Check whether the class method definition sequence complies with the rules.
        '''
        node_infos = []
        for child in node.body:
            if not isinstance(child, astroid.FunctionDef):
                continue
            dec_weight_key = self.check_decorators(child)
            if dec_weight_key is not None:
                self.get_ordering_errors(dec_weight_key, child, node_infos)
                node_infos.append([dec_weight_key, child])
                continue
            if child.name in ('__new__', '__init__', '__post_init__'):
                weight_key = child.name
            else:
                # magic method
                if child.name.startswith('__') and child.name.endswith('__'):
                    weight_key = 'magic_method'
                # private method
                elif child.name.startswith('_'):
                    weight_key = 'private_method'
                else:
                    # common method
                    weight_key = 'method'
            self.get_ordering_errors(weight_key, child, node_infos)
            node_infos.append([weight_key, child])

    def get_ordering_errors(self, weight_key, node, node_infos):
        '''
            Compare the current node with the previously stored node list one by one. If no, an alarm is generated.
            If the weight of the current node is small but the row number is larger than that of the previous node, 
            the sequence is incorrect.
        '''
        weight_value = self.WEIGHT_INFO.get(weight_key, -1)
        for node_weight_key, prev_node in node_infos:
            if weight_key == node_weight_key:
                continue
            node_weight_value = self.WEIGHT_INFO.get(node_weight_key, -1)
            if weight_value < node_weight_value and node.lineno > prev_node.lineno:
                # The alarm information in the same column is output only once, 
                # and the last alarm information is output.
                msg_key = "%d_%d"%(prev_node.lineno, prev_node.col_offset)
                if msg_key not in self.errors:
                    self.errors[msg_key] = [prev_node, node]
                    continue
                if node.lineno > self.errors[msg_key][1].lineno:
                    self.errors[msg_key] = [prev_node, node]

    def pop_errors(self):
        '''
            Output alarm information.
        '''
        for prev_node, node in self.errors.values():
            msg_args = (node.parent.name, prev_node.name, node.parent.name, node.name)
            self.add_message('function-order', node=prev_node, args=msg_args)


def register(linter):
    linter.register_checker(FunctionOrderChecker(linter))
