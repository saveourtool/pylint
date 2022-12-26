# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

from pylint.checkers import BaseChecker, utils
from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker
from astroid import nodes

class LambdaInLoopChecker(BaseChecker):
    __implements__ = IAstroidChecker
    name = 'lambda-in-loop'
    priority = -1
    
    msgs = {
        'H3402': (
            'Cell variable %s defined in loop',
            'lambda-in-loop',
            "A variable used in a closure is defined in a loop. "
            "This will result in all closures using the same value for "
            "the closed-over variable.",
        ),
    }

    def __init__(self, linter=None):
        super().__init__(linter)

    @check_messages('lambda-in-loop')
    def visit_name(self, node: nodes.Name) -> None:
        stmt = node.statement(future=True)
        if stmt.fromlineno is None:
            return

        self._check_late_binding_closure(node)
        
    @staticmethod
    def is_being_called(node_scope) -> bool:
        '''
            Check whether lambda function is called or not.
            if lambda be called, will not pop error message,otherwise pop message
        '''
        def is_lambda_called(scope):
            parent = scope.parent
            if isinstance(parent, nodes.Call):
                parent_func = parent.func
                func_name = ''
                if isinstance(parent_func, nodes.Attribute):
                    func_name = parent_func.attrname
                    if func_name in ('append', 'add'):
                        return False
                elif isinstance(parent_func, nodes.Name):
                    func_name = parent_func.name
                    if func_name == 'map':
                        return is_lambda_called(parent)
            elif isinstance(parent, nodes.Assign):
                return False
            return True
            
        if utils.is_being_called(node_scope):
            return True
        if isinstance(node_scope, nodes.FunctionDef):
            return False
        return is_lambda_called(node_scope)

    def _check_late_binding_closure(self, node: nodes.Name) -> None:
        """Check whether node is a cell var that is assigned within a containing loop.

        Special cases where we don't care about the error:
        1. When the node's function is immediately called, e.g. (lambda: i)()
        2. When the node's function is returned from within the loop, e.g. return lambda: i
        """
        node_scope = node.frame(future=True)
        # If node appears in a default argument expression,
        # look at the next enclosing frame instead
        if utils.is_default_argument(node, node_scope):
            node_scope = node_scope.parent.frame(future=True)

        # Check if node is a cell var
        if (
            not isinstance(node_scope, (nodes.Lambda, nodes.FunctionDef))
            or node.name in node_scope.locals
        ):
            return

        assign_scope, stmts = node.lookup(node.name)
        if not stmts or not assign_scope.parent_of(node_scope):
            return

        if utils.is_comprehension(assign_scope):
            self.add_message("lambda-in-loop", node=node, args=node.name)
        else:
            # Look for an enclosing For loop.
            # Currently, we only consider the first assignment
            assignment_node = stmts[0]

            maybe_for = assignment_node
            while maybe_for and not isinstance(maybe_for, nodes.For):
                if maybe_for is assign_scope:
                    break
                maybe_for = maybe_for.parent
            else:
                if (
                    maybe_for
                    and maybe_for.parent_of(node_scope)
                    and not self.is_being_called(node_scope)
                    and node_scope.parent
                    and not isinstance(node_scope.statement(future=True), nodes.Return)
                ):
                    self.add_message("lambda-in-loop", node=node, args=node.name)
                    

def register(linter):
    linter.register_checker(LambdaInLoopChecker(linter))
