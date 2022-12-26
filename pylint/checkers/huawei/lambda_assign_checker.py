# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

import astroid

from pylint.checkers import BaseChecker
from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker

class LambdaAssignChecker(BaseChecker):
    __implements__ = IAstroidChecker
    name = 'lambda-assign'
    priority = -1
    

    msgs = {
        'H3203': (
            'A lambda expression should not be assigned to a variable',
            'lambda-assign',
            'a regular function should be used'
        ),
    }

    def __init__(self, linter=None):
        super().__init__(linter)

    @check_messages("lambda-assign")
    def visit_assign(self, node):
        self.check_assign_lambda(node)
    
    visit_annassign = visit_assign

    def check_assign_lambda(self, node):
        if isinstance(node.value, astroid.Lambda):
            self.add_message('lambda-assign', node=node)

def register(linter):
    linter.register_checker(LambdaAssignChecker(linter))
