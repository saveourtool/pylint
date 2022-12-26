# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

import re
from typing import List, Tuple

from astroid import nodes


from pylint.checkers import BaseChecker
from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker
from pylint.checkers.variables import in_for_else_branch, FUTURE
from pylint.constants import TYPING_TYPE_CHECKS_GUARDS

# regexp for ignored argument name
IGNORED_ARGUMENT_NAMES = re.compile("_.*|^ignored_|^unused_")

class RedefinedNameChecker(BaseChecker):
    '''
        re-implementation rule W0621 in checker:VariablesChecker
    '''
    __implements__ = IAstroidChecker
    name = 'redefined-name'
    priority = -1
    
    msgs = {
        'H2104': (
            'Redefining name %r from outer scope (line %s)',
            'huawei-redefined-outer-name',
            "Used when a variable's name hides a name defined in the outer scope."
        ),
    }
    
    PYTEST_MODULE_NAME = 'pytest'
    
    options = (
        (
            "huawei-dummy-variables-rgx",
            {
                "default": "_+$|(_[a-zA-Z0-9_]*[a-zA-Z0-9]+?$)|dummy|^ignored_|^unused_",
                "type": "regexp",
                "metavar": "<regexp>",
                "help": "A regular expression matching the name of dummy "
                "variables (i.e. expected to not be used).",
            },
        ),
        (
            "huawei-ignored-argument-names",
            {
                "default": IGNORED_ARGUMENT_NAMES,
                "type": "regexp",
                "metavar": "<regexp>",
                "help": "Argument names that match this expression will be "
                "ignored. Default to name with leading underscore.",
            },
        ),
        )

    def __init__(self, linter=None):
        super().__init__(linter)
        
        self._loop_variables = []
        self._except_handler_names_queue: List[
            Tuple[nodes.ExceptHandler, nodes.AssignName]
        ] = []
        #decoratored names imported from pytest
        self.names = []

    @check_messages("huawei-redefined-outer-name")
    def visit_for(self, node: nodes.For) -> None:
        assigned_to = [a.name for a in node.target.nodes_of_class(nodes.AssignName)]

        # Only check variables that are used
        dummy_rgx = self.config.huawei_dummy_variables_rgx
        assigned_to = [var for var in assigned_to if not dummy_rgx.match(var)]

        for variable in assigned_to:
            for outer_for, outer_variables in self._loop_variables:
                if variable in outer_variables and not in_for_else_branch(
                    outer_for, node
                ):
                    self.add_message(
                        "huawei-redefined-outer-name",
                        args=(variable, outer_for.fromlineno),
                        node=node,
                    )
                    break

        self._loop_variables.append((node, assigned_to))

    @check_messages("huawei-redefined-outer-name")
    def leave_for(self, node: nodes.For) -> None:
        self._loop_variables.pop()
        
    def visit_functiondef(self, node: nodes.FunctionDef) -> None:
        """Visit function: update consumption analysis variable and check locals."""
        if not self.linter.is_message_enabled("huawei-redefined-outer-name"):
            return
        globs = node.root().globals
        for name, stmt in node.items():
            if name in globs and not isinstance(stmt, nodes.Global):
                definition = globs[name][0]
                if (
                    isinstance(definition, nodes.ImportFrom)
                    and definition.modname == FUTURE
                ):
                    # It is a __future__ directive, not a symbol.
                    continue

                # Do not take in account redefined names for the purpose
                # of type checking.:
                if any(
                    isinstance(definition.parent, nodes.If)
                    and definition.parent.test.as_string() in TYPING_TYPE_CHECKS_GUARDS
                    for definition in globs[name]
                ):
                    continue
                    
                # Skip pytest decoratorion
                if self.is_function_decoratored(definition):
                    continue
                    
                line = definition.fromlineno
                if not self._is_name_ignored(stmt, name):
                    self.add_message(
                        "huawei-redefined-outer-name", args=(name, line), node=stmt
                    )

    @check_messages("huawei-redefined-outer-name")
    def visit_excepthandler(self, node: nodes.ExceptHandler) -> None:
        if not node.name or not isinstance(node.name, nodes.AssignName):
            return

        for outer_except, outer_except_assign_name in self._except_handler_names_queue:
            if node.name.name == outer_except_assign_name.name:
                self.add_message(
                    "huawei-redefined-outer-name",
                    args=(outer_except_assign_name.name, outer_except.fromlineno),
                    node=node,
                )
                break

        self._except_handler_names_queue.append((node, node.name))

    @check_messages("huawei-redefined-outer-name")
    def leave_excepthandler(self, node: nodes.ExceptHandler) -> None:
        if not node.name or not isinstance(node.name, nodes.AssignName):
            return
        self._except_handler_names_queue.pop()
        
    def _is_name_ignored(self, stmt, name):
        authorized_rgx = self.config.huawei_dummy_variables_rgx
        if (
            isinstance(stmt, nodes.AssignName)
            and isinstance(stmt.parent, nodes.Arguments)
            or isinstance(stmt, nodes.Arguments)
        ):
            regex = self.config.huawei_ignored_argument_names
        else:
            regex = authorized_rgx
        return regex and regex.match(name)
        
    def is_function_decoratored(self, node: nodes.FunctionDef):
        '''function is decoratored by pytest or not'''
        if not isinstance(node, nodes.FunctionDef):
            return False
        decorators = node.decorators
        if decorators is not None:
            for decorator in decorators.nodes:
                # decorator startswith pytest
                if decorator.as_string().startswith(self.PYTEST_MODULE_NAME + "."):
                    return True
                # decorator name imported from pytest
                if isinstance(decorator, nodes.Name):
                    if decorator.name in self.names:
                        return True
                elif isinstance(decorator, nodes.Call):
                    if decorator.func.as_string() in self.names:
                        return True
        return False

    @check_messages("huawei-redefined-outer-name")
    def visit_importfrom(self, node):
        '''
            collect names imported from pytest
        '''
        if isinstance(node.parent, nodes.Module):
            if node.modname == self.PYTEST_MODULE_NAME:
                for names in node.names:
                    if names[1] is not None:
                        self.names.append(names[1])
                    elif names[0] is not None:
                        self.names.append(names[0])

def register(linter):
    linter.register_checker(RedefinedNameChecker(linter))
