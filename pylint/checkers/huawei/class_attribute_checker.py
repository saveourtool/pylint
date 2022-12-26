# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

from functools import cached_property

import astroid
from astroid import nodes

from pylint.checkers import BaseChecker
from pylint.checkers.utils import check_messages, is_property_setter
from pylint.interfaces import IAstroidChecker
from pylint.utils import get_global_option
from pylint.checkers.classes.class_checker import _called_in_methods

class ClassAttributeChecker(BaseChecker):
    '''
        re-implementation checker of pylint\checkers\classes\class_checker.py
    '''
    __implements__ = IAstroidChecker
    name = 'class-attribute-defined-outside-init'
    priority = -1
    
    msgs = {
        'H3608': (
            "Class attribute %r defined outside __init__",
            "class-attribute-defined-outside-init",
            "Used when an instance attribute is defined outside the __init__ method.",
        ),
    }

    def __init__(self, linter=None):
        super().__init__(linter)
        
    def open(self) -> None:
        self._mixin_class_rgx = get_global_option(self, "mixin-class-rgx")
        self.defining_attr_methods = list(get_global_option(self, "defining-attr-methods"))

    @cached_property
    def _ignore_mixin(self):
        return get_global_option(self, "ignore-mixin-members", default=True)
 
    @check_messages("class-attribute-defined-outside-init")
    def leave_classdef(self, node: nodes.ClassDef) -> None:
        """Checker for Class nodes.
        check that instance attributes are defined in __init__
        """
        self._check_attribute_defined_outside_init(node)

    def _check_attribute_defined_outside_init(self, cnode: nodes.ClassDef) -> None:
        # check access to existent members on non metaclass classes
        if self._ignore_mixin and self._mixin_class_rgx.match(cnode.name):
            # We are in a mixin class. No need to try to figure out if
            # something is missing, since it is most likely that it will
            # miss.
            return
        # checks attributes are defined in an allowed method such as __init__
        if not self.linter.is_message_enabled("class-attribute-defined-outside-init"):
            return
        current_module = cnode.root()
        defined_attrs = []
        outside_attrs = []
        called_methods = set()
        for attr, nodes_lst in cnode.instance_attrs.items():
            # Exclude `__dict__` as it is already defined.
            if attr == "__dict__":
                continue

            # Skip nodes which are not in the current module and it may screw up
            # the output, while it's not worth it
            nodes_lst = [
                n
                for n in nodes_lst
                if not isinstance(
                    n.statement(future=True), (nodes.Delete, nodes.AugAssign)
                )
                and n.root() is current_module
            ]
            if not nodes_lst:
                continue  # error detected by typechecking

            # Check if any method attr is defined in is a defining method
            # or if we have the attribute defined in a setter.
            frames = (node.frame(future=True) for node in nodes_lst)
            if any(
                frame.name in self.defining_attr_methods or is_property_setter(frame)
                for frame in frames
            ):
                continue

            # check attribute is defined in a parent's __init__
            for parent in cnode.instance_attr_ancestors(attr):
                attr_defined = False
                # check if any parent method attr is defined in is a defining method
                for node in parent.instance_attrs[attr]:
                    if node.frame(future=True).name in self.defining_attr_methods:
                        attr_defined = True
                if attr_defined:
                    # we're done :)
                    break
            else:
                # check attribute is defined as a class attribute
                try:
                    cnode.local_attr(attr)
                except astroid.NotFoundError:
                    if attr not in defined_attrs:
                        for node in nodes_lst:
                            func = node.frame(future=True)
                            if func.name not in self.defining_attr_methods:
                                # If the attribute was set by a call in any
                                # of the defining methods, then don't emit
                                # the warning.
                                if _called_in_methods(
                                    func, cnode, self.defining_attr_methods + list(called_methods)
                                ):
                                    # attr defined in called methods is allowed
                                    defined_attrs.append(attr)
                                    # attr in chain methods called in __init__ is allowed
                                    called_methods.add(func.name)
                                    continue
                                outside_attrs.append((attr, node))
        for attr, node in outside_attrs:
            # attr defined in called methods will not pop error
            if attr in defined_attrs:
                continue
            self.add_message(
                "class-attribute-defined-outside-init", args=attr, node=node
            )

def register(linter):
    linter.register_checker(ClassAttributeChecker(linter))
