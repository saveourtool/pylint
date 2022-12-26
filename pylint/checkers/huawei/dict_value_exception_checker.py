# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

import re
from typing import Set, Tuple

import astroid
from astroid import nodes

from pylint.checkers import BaseChecker, utils
from pylint.interfaces import IAstroidChecker
import pylint.checkers.huawei.utils.util as huawei_util


class DictValueExceptionChecker(BaseChecker):
    __implements__ = IAstroidChecker
    name = 'dict-value-exception'
    priority = -4
    msgs = {
        "H3107": (
            "dict[key] must be use get() or KeyError exception",
            "get-dict-value-exception",
            "Do not directly use dict[key] to obtain values from the dictionary. If "
            "dict[key] must be used, pay attention to exception capture and processing "
            "when key is not in dict.",
        ),
    }

    def __init__(self, linter=None):
        super(DictValueExceptionChecker, self).__init__(linter)
        self.subscript_list = []
        self.tryexcept_list = []
        self.safe_set: Set[Tuple[str, str]] = set()
        self.const_pattern = re.compile(r'[A-Z_]+')
        
    @staticmethod
    def is_dict_or_keys_name(node: nodes.NodeNG, dict_name: str) -> bool:
        '''
        Return True if node string is dict name or dict.keys() 
    
        :param node: Node considered
        :type node: astroid.Node
        
        :param dict_name: dict name
        :type dict_name: str
        :return: True if node string is dict name or dict.keys()
        :rtype: bool
        '''
        node_string = node.as_string()
        return  node_string == dict_name or node_string == dict_name + ".keys()"

    @utils.check_messages("get-dict-value-exception")
    def visit_subscript(self, node):
        node_type = huawei_util.node_type(node.value)
        if (node.ctx != astroid.Load) or \
                (node_type is not astroid.Dict) or \
                self.is_in_safe_context(node):
            return

        self.subscript_list.append(node)
        if (
            self.subscript_list and self.tryexcept_list and
            self.subscript_list[-1].lineno > self.tryexcept_list[-1][0] and
            self.subscript_list[-1].lineno < self.tryexcept_list[-1][1]
        ):
            self.subscript_list.pop(-1)

    def is_in_safe_context(self, node: astroid.Subscript):
        dict_name = self.get_dict_name(node)
        slice_name = self.get_slice_name(node)
        if (not dict_name) or (not slice_name):
            return False
        # references to a const dict (with CAP_WORDS style naming) are safe.
        if self.const_pattern.match(dict_name):
            return True

        if (dict_name, slice_name) in self.safe_set:
            return True

        parent_scope = self.get_parent_scope(node)
        # check whether this subscript is inside a ite-expression.
        # e.g. dict[key] if key in dict else None
        if isinstance(parent_scope, astroid.IfExp):
            return self.is_if_guard(parent_scope, dict_name, slice_name, ['in', 'not in'])
        # check 'if k not in d' exists before current node.
        if self.check_brothers(parent_scope, dict_name, slice_name, (node.fromlineno, node.col_offset)):
            return True

        cur_node = node.parent if hasattr(node, 'parent') else None
        # recursively check parent nodes.
        while self.is_in_domain(cur_node):
            if self.is_guard(cur_node, dict_name, slice_name):
                return True
            if hasattr(cur_node, 'parent'):
                cur_node = cur_node.parent
            else:
                break

    def check_brothers(self, parent_scope, dict_name, slice_name, offset):
        if not parent_scope:
            return False

        try:
            for stmt in parent_scope.body:
                if self.is_not_in_guard(stmt, dict_name, slice_name, offset):
                    return True
        # in case parent_scope's body is None or other non-iterable objects.
        except TypeError:
            return False
        # recursively check parent scope.
        if isinstance(parent_scope, (astroid.FunctionDef, astroid.ClassDef, astroid.Module)) or \
                not hasattr(parent_scope, 'parent'):
            return False
        next_parent = self.get_parent_scope(parent_scope.parent)
        return self.check_brothers(next_parent, dict_name, slice_name, offset)

    def get_dict_name(self, node: astroid.Subscript):
        return node.value.as_string()

    def get_slice_name(self, node: astroid.Subscript):
        return node.slice.as_string()

    def is_in_domain(self, node):
        return not isinstance(node, (astroid.FunctionDef, astroid.ClassDef, astroid.Module))

    def get_parent_scope(self, node):
        if isinstance(node, (astroid.FunctionDef, astroid.ClassDef, astroid.Module)):
            return node
        if hasattr(node, 'body') and node.body:
            return node
        if not hasattr(node, 'parent'):
            return None
        return self.get_parent_scope(node.parent)

    def is_guard(self, stmt, dict_name, slice_name):
        if self.is_if_guard(stmt, dict_name, slice_name, ['in']):
            return True

        if isinstance(stmt, astroid.For) and stmt.target and stmt.iter:
            return stmt.target.as_string() == slice_name and self.is_dict_or_keys_name(stmt.iter, dict_name)
        return False

    def is_not_in_guard(self, stmt, dict_name, slice_name, offset):
        return self.is_if_guard(stmt, dict_name, slice_name, ['not in']) and \
            (stmt.fromlineno, stmt.col_offset) < offset

    @utils.check_messages("get-dict-value-exception")
    def visit_assign(self, node):
        # assign dict all items
        if isinstance(node.value, astroid.Dict):
            for dictname in node.targets:
                for keyname, _ in node.value.items:
                    self.safe_set.add((dictname.as_string(), keyname.as_string()))
        # assign dict slice items
        self.add_dict_slice_items(node)
    
    def add_dict_slice_items(self, node):
        '''
            collect dict slice items, such as:
            d1 = {}
            d1[1] = 2
            d1['a'] = 'b'
            d1[2] = 5
        '''
        for target in node.targets:
            if isinstance(target, astroid.Subscript):
                target_node_type = huawei_util.node_type(target.value)
                if (target.ctx != astroid.Store) or \
                        (target_node_type is not astroid.Dict):
                    return
                dict_name = self.get_dict_name(target)
                self.safe_set.add((dict_name, target.slice.as_string()))

    @utils.check_messages("get-dict-value-exception")
    def visit_classdef(self, node):
        '''
            collect all class scope dict slice items in class function nodes
        '''
        for class_child in node.body:
            if isinstance(class_child, nodes.FunctionDef):
                for func_child in class_child.body:
                    if isinstance(func_child, nodes.Assign):
                        self.add_dict_slice_items(func_child)
        
    def is_if_guard(self, stmt, dict_name, slice_name, predicates):
        if not isinstance(stmt, (astroid.If, astroid.IfExp)):
            return False
        
        if isinstance(stmt.test, astroid.Compare):
            return self.is_compare_guard(stmt.test, dict_name, slice_name, predicates)
        
        if isinstance(stmt.test, astroid.BoolOp):
            return self.is_boolop_guard(stmt.test, dict_name, slice_name, predicates)
        return False

    def is_compare_guard(self, stmt:astroid.Compare, dict_name, slice_name, predicates):
        if not isinstance(stmt, astroid.Compare):
            return False
        op = stmt.ops[0]
        return stmt.left.as_string() == slice_name and \
                len(op) == 2 and \
                op[0] in predicates and \
                self.is_dict_or_keys_name(op[1], dict_name)

    def is_boolop_guard(self, stmt:astroid.BoolOp, dict_name, slice_name, predicates):
        if not isinstance(stmt, astroid.BoolOp) or stmt.op != 'and':
            return False
        for subc in stmt.values:
            if self.is_compare_guard(subc, dict_name, slice_name, predicates) or \
                self.is_boolop_guard(subc, dict_name, slice_name, predicates):
                return True
        return False

    @utils.check_messages("get-dict-value-exception")
    def visit_tryexcept(self, node):
        self._check_get_dict_value_in_tryexcept(node)

    def _check_get_dict_value_in_tryexcept(self, node):
        for handler in node.handlers:
            if (
                handler.type is not None and
                type(handler.type) is astroid.Name and
                handler.type.name == "KeyError"
            ):
                self.tryexcept_list.append([node.fromlineno, node.tolineno])

    @utils.check_messages("get-dict-value-exception")
    def leave_functiondef(self, node):
        self.tryexcept_list = []
        # if parent of func node is class node, the safe_set variable is valid in class scope
        if isinstance(node.parent, nodes.ClassDef):
            return
        self.safe_set = set()

    @utils.check_messages("get-dict-value-exception")
    def leave_classdef(self, node):
        # leave class scope, clear safe_set variable
        self.safe_set = set()
        self.tryexcept_list = []

    def leave_module(self, _):
        for mess in self.subscript_list:
            self.add_message("get-dict-value-exception", node=mess)
        self.subscript_list = []
        self.tryexcept_list = []


def register(linter):
    linter.register_checker(DictValueExceptionChecker(linter))
