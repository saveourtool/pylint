# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

import astroid

from pylint.checkers import BaseChecker
from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker
import pylint.checkers.huawei.utils.util as huawei_util


class ImportPositionChecker(BaseChecker):
    __implements__ = IAstroidChecker
    name = 'import-position'
    priority = -1
    
    msgs = {
        'H2305': (
            'Import "%s" should be placed at the top of the module',
            'huawei-wrong-import-position',
            'Imports should be placed after module comments and document strings,'
            'and before module global variable and constant declarations.'
        )
    }

    def __init__(self, linter=None):
        super().__init__(linter)
        self._first_non_import_node = None

    @check_messages("import-position")
    def visit_import(self, node):
        if isinstance(node.parent, astroid.Module):
            # Allow imports nested
            self._check_position(node)

    @check_messages("import-position")
    def visit_importfrom(self, node):
        if isinstance(node.parent, astroid.Module):
            # Allow imports nested
            self._check_position(node)

    def compute_first_non_import_node(self, node):
        if not self.linter.is_message_enabled("huawei-wrong-import-position", node.fromlineno):
            return
        # if the node does not contain an import instruction, and if it is the
        # first node of the module, keep a track of it (all the import positions
        # of the module will be compared to the position of this first
        # instruction)
        if self._first_non_import_node:
            return
        if not isinstance(node.parent, astroid.Module):
            return
        nested_allowed = [astroid.TryExcept, astroid.TryFinally]
        is_nested_allowed = [
            allowed for allowed in nested_allowed if isinstance(node, allowed)
        ]
        if is_nested_allowed and any(
            node.nodes_of_class((astroid.Import, astroid.ImportFrom))
        ):
            return
        if isinstance(node, astroid.Assign):
            # Add compatibility for module level dunder names
            # https://www.python.org/dev/peps/pep-0008/#module-level-dunder-names
            valid_targets = [
                isinstance(target, astroid.AssignName)
                and target.name.startswith("__")
                and target.name.endswith("__")
                for target in node.targets
            ]
            if all(valid_targets):
                return
        # skip sys.path.append and monkey patch statement
        if isinstance(node, astroid.Expr) and isinstance(node.value, astroid.Call):
            func = node.value.func
            attribute_name = huawei_util.get_attribute_name(func)
            if attribute_name in ['sys.path.append', 'sys.path.insert', 'eventlet.monkey_path', 
                                                'monkey.patch_all', 'gevent.monkey.patch_all']:
                return

        self._first_non_import_node = node

    visit_tryfinally = (
        visit_tryexcept
    ) = (
        visit_assignattr
    ) = (
        visit_assign
    ) = (
        visit_ifexp
    ) = visit_comprehension = visit_expr = visit_if = compute_first_non_import_node

    def visit_functiondef(self, node):
        if not self.linter.is_message_enabled("huawei-wrong-import-position", node.fromlineno):
            return
        # If it is the first non import instruction of the module, record it.
        if self._first_non_import_node:
            return

        # Check if the node belongs to an `If` or a `Try` block. If they
        # contain imports, skip recording this node.
        if not isinstance(node.parent.scope(), astroid.Module):
            return

        root = node
        while not isinstance(root.parent, astroid.Module):
            root = root.parent

        if isinstance(root, (astroid.If, astroid.TryFinally, astroid.TryExcept)):
            if any(root.nodes_of_class((astroid.Import, astroid.ImportFrom))):
                return

        self._first_non_import_node = node

    visit_classdef = visit_for = visit_while = visit_functiondef

    def _check_position(self, node):
        """Check `node` import or importfrom node position is correct

        Send a message  if `node` comes before another instruction
        """
        # if a first non-import instruction has already been encountered,
        # it means the import comes after it and therefore is not well placed
        if self._first_non_import_node:
            self.add_message("huawei-wrong-import-position", node=node, args=node.as_string())

    def leave_module(self, node):
        self._first_non_import_node = None


def register(linter):
    linter.register_checker(ImportPositionChecker(linter))
