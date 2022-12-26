import sys

import astroid
from astroid import nodes

from pylint.checkers import BaseChecker
from pylint.checkers.utils import check_messages, is_attr_private, is_property_setter
from pylint.interfaces import IAstroidChecker
from pylint.checkers.classes.class_checker import _different_parameters
from pylint.utils import get_global_option

if sys.version_info >= (3, 8):
    from functools import cached_property
else:
    from astroid.decorators import cachedproperty as cached_property

class ArgumentsChecker(BaseChecker):
    __implements__ = IAstroidChecker
    name = 'arguments'
    priority = -1
    
    msgs = {
        'H3602': (
            "%s %s %r method",
            "huawei-arguments-differ",
            "Used when a method has a different number of arguments than in "
            "the implemented interface or in an overridden method. Extra arguments "
            "with default values are ignored.",
        ),
    }

    def __init__(self, linter=None):
        super().__init__(linter)
        
    @cached_property
    def _dummy_rgx(self):
        return get_global_option(self, "dummy-variables-rgx", default=None)

    def visit_functiondef(self, node: nodes.FunctionDef) -> None:
        """Check method arguments, overriding."""
        # ignore actual functions
        if not node.is_method():
            return

        # 'is_method()' is called and makes sure that this is a 'nodes.ClassDef'
        klass = node.parent.frame(future=True)  # type: nodes.ClassDef
        if node.name == "__init__":
            return
        # check signature if the method overloads inherited method
        for overridden in klass.local_attr_ancestors(node.name):
            # get astroid for the searched method
            try:
                parent_function = overridden[node.name]
            except KeyError:
                # we have found the method but it's not in the local
                # dictionary.
                # This may happen with astroid build from living objects
                continue
            if not isinstance(parent_function, nodes.FunctionDef):
                continue
            self._check_signature(node, parent_function, "overridden", klass)
            break

    visit_asyncfunctiondef = visit_functiondef
    
    def _check_signature(self, method1, refmethod, class_type, cls):
        """Check that the signature of the two given methods match."""
        if not (
            isinstance(method1, nodes.FunctionDef)
            and isinstance(refmethod, nodes.FunctionDef)
        ):
            return

        instance = cls.instantiate_class()
        method1 = astroid.scoped_nodes.function_to_method(method1, instance)
        refmethod = astroid.scoped_nodes.function_to_method(refmethod, instance)

        # Don't care about functions with unknown argument (builtins).
        if method1.args.args is None or refmethod.args.args is None:
            return

        # Ignore private to class methods.
        if is_attr_private(method1.name):
            return
        # Ignore setters, they have an implicit extra argument,
        # which shouldn't be taken in consideration.
        if is_property_setter(method1):
            return

        arg_differ_output = _different_parameters(
            refmethod, method1, dummy_parameter_regex=self._dummy_rgx
        )
        if len(arg_differ_output) > 0:
            for msg in arg_differ_output:
                if "Number" in msg:
                    total_args_method1 = len(method1.args.args)
                    if method1.args.vararg:
                        total_args_method1 += 1
                    if method1.args.kwarg:
                        total_args_method1 += 1
                    if method1.args.kwonlyargs:
                        total_args_method1 += len(method1.args.kwonlyargs)
                    total_args_refmethod = len(refmethod.args.args)
                    if refmethod.args.vararg:
                        total_args_refmethod += 1
                    if refmethod.args.kwarg:
                        total_args_refmethod += 1
                    if refmethod.args.kwonlyargs:
                        total_args_refmethod += len(refmethod.args.kwonlyargs)
                    # if parent class refmethod have variable parameter, ignore number of arguments 
                    if refmethod.args.vararg or refmethod.args.kwarg:
                        continue
                    msg_args = (
                        msg
                        + f"was {total_args_refmethod} in '{refmethod.parent.frame().name}.{refmethod.name}' and "
                        f"is now {total_args_method1} in",
                        class_type,
                        f"{method1.parent.frame().name}.{method1.name}",
                    )
                elif "renamed" in msg:
                    continue
                else:
                    msg_args = (
                        msg,
                        class_type,
                        f"{method1.parent.frame().name}.{method1.name}",
                    )
                self.add_message("huawei-arguments-differ", args=msg_args, node=method1)

def register(linter):
    linter.register_checker(ArgumentsChecker(linter))
