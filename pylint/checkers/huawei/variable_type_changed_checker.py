# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

import collections
from functools import lru_cache

from astroid import nodes
from astroid.bases import Instance

from pylint.checkers import BaseChecker, utils
from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker


class VariableTypeChangedChecker(BaseChecker):
    __implements__ = IAstroidChecker
    name = 'variables'
    priority = -1
    msgs = {
        "W0643": (
            "Prevents variable '%s' changing from type (%s) to (%s) during its life cycle.",
            "variable-type-changed",
            "Prevents variable object types from changing during its life cycle."
        ),
    }

    KNOWN_TYPES = (
        nodes.Tuple,
        nodes.List,
        nodes.Set,
        nodes.Dict
    )

    def __init__(self, linter=None):
        super().__init__(linter)
        # initial variable types
        self.variable_types = collections.defaultdict()
        self.const_cls = collections.defaultdict()
        # init const types
        self.init_const_types()

    @staticmethod
    def get_assign_name(target):
        name = None
        if isinstance(target, nodes.AssignName):
            name = target.name
        elif isinstance(target, nodes.AssignAttr):
            name = target.as_string()
        return name

    def get_comprehension_scope_type(self, scope_node):
        if isinstance(scope_node, nodes.DictComp):
            return self.const_cls['dict']
        elif isinstance(scope_node, nodes.ListComp):
            return self.const_cls['list']
        elif isinstance(scope_node, nodes.SetComp):
            return self.const_cls['set']
        return None

    @staticmethod
    def get_target_type_name(target_type):
        if isinstance(target_type, nodes.Const):
            return target_type.name
        elif target_type is nodes.List:
            return 'list'
        elif target_type is nodes.Tuple:
            return 'tuple'
        elif target_type is nodes.Dict:
            return 'dict'
        elif target_type is nodes.Set:
            return 'set'
        else:
            return 'unkown_type'

    def init_const_types(self):
        self.const_cls.update({
            'list': nodes.List,
            'tuple': nodes.Tuple,
            'dict': nodes.Dict,
            'set': nodes.Set,
            'List': nodes.List,
            'Tuple': nodes.Tuple,
            'Dict': nodes.Dict,
            'Set': nodes.Set
        })
        klasses = {'bool': False, 'int': 1, 'float': 0.0, 'str': '', 'bytes': b'1'}
        for kls, v in klasses.items():
            self.const_cls[kls] = nodes.Const(v)

    @check_messages("variable-type-changed")
    def visit_assign(self, node):
        self.check_assign_types(node)

    @check_messages("variable-type-changed")
    def visit_annassign(self, node):
        '''
        Check annassign statement
        a:int = 3
        b:Tuple = (1,2)
        c:List = [3,4]
        d:set = set()
        '''
        def get_subscript_node_type(node_value):
            '''
                标注类型:
                a: Dict[Any, Any]
                b: typing.Dict[Any, Any]
            '''
            if isinstance(node_value, nodes.Name):
                return node_value.name
            elif isinstance(node_value, nodes.Attribute):
                return node_value.attrname
            return None
        node_type = None
        if isinstance(node.annotation, nodes.Name):
            node_type = node.annotation.name
        elif isinstance(node.annotation, nodes.Subscript):
            node_type = get_subscript_node_type(node.annotation.value)
        name = self.get_assign_name(node.target)
        if node_type in self.const_cls and name is not None:
            if name not in self.variable_types:
                self.variable_types[name] = self.const_cls[node_type]
            else:
                type_changed, _ = self.check_variable_type_changed(
                    node, name, self.const_cls[node_type])
                if type_changed:
                    return
        self.check_target_value_types(node, [node.target], [node.value])

    def check_assign_types(self, node):
        '''
        Check assign statement
        a = 1
        b = "ss"
        '''
        values = [node.value]
        targets = node.targets
        # for statements like x,y = 1,2
        if isinstance(targets[0], nodes.Tuple):
            if len(targets) != 1:
                # A complex assignment, so bail out early.
                return
            targets = targets[0].elts
            if len(targets) == 1:
                # Unpacking a variable into the same name.
                return
            if isinstance(node.value, nodes.Tuple):
                rhs_count = len(node.value.elts)
                if len(targets) != rhs_count or rhs_count == 1:
                    return
                values = node.value.elts
            else:
                return
        self.check_target_value_types(node, targets, values)

    def check_target_value_types(self, node, targets, values):
        '''
        Check whether the variable type changed,like below expressions
        c: float = 12
        c = 23
        str1: str = 90
        str1 = 9
        g: List = {}
        g2: tuple = []

        :param targets: variable name
        :type targets: list
        :param values: variable values
        :type values: list
        :return: 
        :rtype: None
        '''
        for target, value in zip(targets, values):
            name = self.get_assign_name(target)
            if name is None:
                continue
            type_changed, node_type = self.check_variable_type_changed(
                node, name, value)
            if type_changed:
                continue
            if node_type == nodes.Unknown and value is not None:
                # if node type unkown, use inferred type
                node_type = utils.node_type(value)
                if node_type is None:
                    continue
                self.check_variable_type_changed(node, name, node_type)

    def check_variable_type_changed(self, node, name: str, value):
        '''
        Return whether variable type change or not and new variable type
        if variable type could not be inferred, return unkown type

        :param name: variable name
        :type name: str

        :param value: new variable value
        :type value: nodes.Node
        :return: true and new variable type if variable type changed else false 
        :rtype: tuple
        '''
        def _is_none_const(node) -> bool:
            return isinstance(node, nodes.Const) and node.value is None
        target_val = value
        # skip None value
        if _is_none_const(target_val):
            return False, nodes.Const
        # handle const value,such as int,str,float ...
        elif isinstance(target_val, nodes.Const):
            # save varirable value types
            if not self.is_variable_type_saved(name, target_val):
                return False, nodes.Const
            const_type_name = target_val.name
            if self.check_target_const_type_changed(node, name, const_type_name):
                return True, nodes.Const
        # handle known type values, such as list, tuple, set values ...
        elif isinstance(target_val, self.KNOWN_TYPES):
            target_val_type = type(target_val)
            # save varirable value types
            if not self.is_variable_type_saved(name, target_val_type):
                return False, target_val_type
            if self.check_target_type_changed(node, name, target_val_type):
                return True, target_val_type
        # handle known types, such as list, tuple, set ...
        elif target_val in self.KNOWN_TYPES:
            if self.check_target_type_changed(node, name, target_val):
                return True, target_val
        elif isinstance(target_val, Instance):
            builtin_type = target_val.pytype().replace('builtins.', '')
            if builtin_type in self.const_cls:
                target_instance_type = self.const_cls[builtin_type]
                # save varirable value types
                if not self.is_variable_type_saved(name, target_instance_type):
                    return False, target_instance_type
                return self.check_variable_type_changed(node, name, target_instance_type)
        elif isinstance(target_val, nodes.ComprehensionScope):
            target_val_type = self.get_comprehension_scope_type(target_val)
            # save varirable value types
            if not self.is_variable_type_saved(name, target_val_type):
                return False, target_val_type
            return self.check_variable_type_changed(node, name, target_val_type)
        # unkown type
        return False, nodes.Unknown

    def is_variable_type_saved(self, name, val_type):
        '''
            save and check variable type
        '''
        if name not in self.variable_types:
            self.variable_types[name] = val_type
            return False
        return True

    def check_target_type_changed(self, node, name, target_type):
        last_target_type = self.variable_types[name]
        if isinstance(last_target_type, nodes.Const) or (
            last_target_type in self.KNOWN_TYPES and last_target_type != target_type
        ):
            self.add_message(
                "variable-type-changed",
                node=node,
                args=(
                    name,
                    self.get_target_type_name(last_target_type),
                    self.get_target_type_name(target_type)
                )
            )
            return True
        return False

    def check_target_const_type_changed(self, node, name, const_type):
        last_target_type = self.variable_types[name]
        if last_target_type in self.KNOWN_TYPES or (
            isinstance(last_target_type,
                       nodes.Const) and const_type != last_target_type.name
        ):
            self.add_message(
                "variable-type-changed",
                node=node,
                args=(
                    name,
                    self.get_target_type_name(last_target_type),
                    const_type
                )
            )
            return True
        return False

    @utils.check_messages("variable-type-changed")
    def leave_functiondef(self, node):
        # if parent of func node is class node, the variable_types variable is valid in class scope
        if isinstance(node.parent, nodes.ClassDef):
            self.clear_local_variable_types()
            return
        self.variable_types = collections.defaultdict()

    @utils.check_messages("variable-type-changed")
    def leave_classdef(self, node):
        # leave class scope, clear variable_types variable
        self.variable_types = collections.defaultdict()

    def leave_module(self, _):
        self.variable_types = collections.defaultdict()

    def clear_local_variable_types(self):
        '''
            clear method local variable types when leave method
        '''
        clear_variable_types = []
        for name in self.variable_types:
            if name.find('self.') == -1:
                clear_variable_types.append(name)
        for name in clear_variable_types:
            self.variable_types.pop(name)


def register(linter):
    """required method to auto register this checker"""
    linter.register_checker(VariableTypeChangedChecker(linter))
