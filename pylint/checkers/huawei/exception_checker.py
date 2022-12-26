# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

import itertools 

import astroid
from astroid import nodes, objects

from pylint.checkers import BaseChecker
from pylint.checkers.utils import check_messages
from pylint.checkers import utils
from pylint.interfaces import IAstroidChecker
from pylint.checkers.exceptions import BaseVisitor

class ExceptionChecker(BaseChecker):
    __implements__ = IAstroidChecker
    name = 'exception'
    priority = -1
    
    msgs = {
        'H3704': (
            "Consider explicitly re-raising using the 'from' keyword",
            "huawei-raise-missing-from",
            "Python 3's exception chaining means it shows the traceback of the "
            "current exception, but also the original exception. Not using `raise "
            "from` makes the traceback inaccurate, because the message implies "
            "there is a bug in the exception-handling code itself, which is a "
            "separate situation than wrapping an exception.",
        ),
        "H3703": (
            "Raising a new style class which doesn't inherit from Exception",
            "huawei-raising-non-exception",
            "Used when a new style class which doesn't inherit from "
            "Exception is raised.",
        ),
        "H3710": (
            "NotImplemented raised - should raise NotImplementedError",
            "huawei-notimplemented-raised",
            "Used when NotImplemented is raised instead of NotImplementedError",
        ),
    }

    def __init__(self, linter=None):
        super().__init__(linter)

    @check_messages(
        "huawei-raise-missing-from",
        "huawei-raising-non-exception",
        "huawei-notimplemented-raised"
    )
    def visit_raise(self, node: nodes.Raise) -> None:
        if node.exc is None:
            return
        if node.cause is None:
            self._check_raise_missing_from(node)
            
        expr = node.exc
        ExceptionRaiseRefVisitor(self, node).visit(expr)

        inferred = utils.safe_infer(expr)
        if inferred is None or inferred is astroid.Uninferable:
            return
        ExceptionRaiseLeafVisitor(self, node).visit(inferred)

    def _check_raise_missing_from(self, node: nodes.Raise) -> None:
        if node.exc is None:
            # This is a plain `raise`, raising the previously-caught exception. No need for a
            # cause.
            return
        # We'd like to check whether we're inside an `except` clause:
        containing_except_node = utils.find_except_wrapper_node_in_scope(node)
        if not containing_except_node:
            return
        # We found a surrounding `except`! We're almost done proving there's a
        # `raise-missing-from` here. The only thing we need to protect against is that maybe
        # the `raise` is raising the exception that was caught, possibly with some shenanigans
        # like `exc.with_traceback(whatever)`. We won't analyze these, we'll just assume
        # there's a violation on two simple cases: `raise SomeException(whatever)` and `raise
        # SomeException`.
        if containing_except_node.name is None:
            # The `except` doesn't have an `as exception:` part, meaning there's no way that
            # the `raise` is raising the same exception.
            self.add_message("huawei-raise-missing-from", node=node)
        elif isinstance(node.exc, nodes.Call) and isinstance(node.exc.func, nodes.Name):
            # We have a `raise SomeException(whatever)`.
            self.add_message("huawei-raise-missing-from", node=node)
        elif (
            isinstance(node.exc, nodes.Name)
            and node.exc.name != containing_except_node.name.name
        ):
            # We have a `raise SomeException`.
            self.add_message("huawei-raise-missing-from", node=node)
            
class ExceptionRaiseRefVisitor(BaseVisitor):
    """Visit references (anything that is not an AST leaf)."""

    def visit_name(self, node: nodes.Name) -> None:
        if node.name == "NotImplemented":
            self._checker.add_message("huawei-notimplemented-raised", node=self._node)
            
    def visit_call(self, node: nodes.Call) -> None:
        if isinstance(node.func, nodes.Name):
            self.visit_name(node.func)


class ExceptionRaiseLeafVisitor(BaseVisitor):
    """Visitor for handling leaf kinds of a raise value."""

    def visit_instance(self, instance: objects.ExceptionInstance) -> None:
        cls = instance._proxied
        self.visit_classdef(cls)

    # Exception instances have a particular class type
    visit_exceptioninstance = visit_instance

    def visit_classdef(self, node: nodes.ClassDef) -> None:
        if not inherit_from_std_ex(node) and utils.has_known_bases(node):
            if node.newstyle:
                self._checker.add_message("huawei-raising-non-exception", node=self._node)
                

def inherit_from_std_ex(node: nodes.NodeNG) -> bool:
    """Return whether the given class node is subclass of
    exceptions.Exception.
    """
    ancestors = node.ancestors() if hasattr(node, "ancestors") else []
    return any(
        ancestor.name in {"Exception"}
        and ancestor.root().name == utils.EXCEPTIONS_MODULE
        for ancestor in itertools.chain([node], ancestors)
    )

def register(linter):
    linter.register_checker(ExceptionChecker(linter))
