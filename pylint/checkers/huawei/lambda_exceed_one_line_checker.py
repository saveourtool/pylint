# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

from pylint.checkers import BaseChecker
from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker

class LambdaExceedOneLineChecker(BaseChecker):
    __implements__ = IAstroidChecker
    name = 'lambda-exceed-one-line'
    priority = -1
	
    msgs = {
        'H3202': (
            'Lambda function should not exceed one line.',
            'lambda-exceed-one-line',
            'Complicate lambda function are hard to understand.'
        ),
    }

    def __init__(self, linter=None):
        super(LambdaExceedOneLineChecker, self).__init__(linter)

    @check_messages("lambda-exceed-one-line")
    def visit_lambda(self, node):
        self.check_lambda(node)

    def check_lambda(self, node):
        if node.fromlineno != node.tolineno:
            self.add_message('lambda-exceed-one-line', node=node)
        
            

def register(linter):
    linter.register_checker(LambdaExceedOneLineChecker(linter))
