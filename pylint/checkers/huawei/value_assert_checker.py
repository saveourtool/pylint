# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

import astroid

from pylint.checkers import BaseChecker, utils
from pylint.interfaces import IAstroidChecker
from pylint.checkers.stdlib import UNITTEST_CASE


class ValueAssertChecker(BaseChecker):
    __implements__ = IAstroidChecker
    name = 'value-assert'
    priority = -1

    # Replacement asserts for different operators.
    replacements = {
        "==": "assertEqual or assertNotEqual",
        "!=": "assertEqual or assertNotEqual",
        ">": "assertGreater or assertLess",
        "<": "assertGreater or assertLess",
        "in": "assertIn or assertNotIn",
        "not in": "assertIn or assertNotIn"
    }
    msgs = {
        "H4702": ( # python 3.0 standard 3.17 G.TES.02
            "Improper use of %s, you are supposed to replace it with %s.",
            "improper-value-assert",
            "Check improper use of value assert statements..",
        ),
    }

    def __init__(self, linter=None):
        super(ValueAssertChecker, self).__init__(linter)

    @utils.check_messages("improper-value-assert")
    def visit_call(self, node):
        try:
            for inferred in node.func.infer():
                if inferred is astroid.Uninferable:
                    continue
                if inferred.root().name == UNITTEST_CASE:
                    self._check_improper_assert(node, inferred)
        except astroid.InferenceError:
            return

    def _is_assert_bool(self, node, inferred):
        return (
            inferred.name == "assertEqual" and
            len(node.args) >= 2 and
            isinstance(node.args[1], astroid.Const) and
            isinstance(node.args[1].value, bool))

    def _is_assert_compare(self, node, inferred):
        return (
            inferred.name in ["assertTrue", "assertFalse"]
            and len(node.args) >= 1
            and isinstance(node.args[0], astroid.Compare))

    def _is_assert_instance(self, node, inferred):
        return (
            inferred.name in ["assertTrue", "assertFalse"]
            and len(node.args) >= 1
            and isinstance(node.args[0], astroid.Call)
            and isinstance(node.args[0].func, astroid.Name)
            and node.args[0].func.name == "isinstance")

    def _is_compare_to_none(self, assert_ops):
        # assert_ops contains right-hand values of the compare.
        return (
            assert_ops[0] in ["is", "is not"] and 
            isinstance(assert_ops[1], astroid.Const) and 
            assert_ops[1].value is None)

    def _add_assert_message(self, node, inferred, replacement_str):
        self.add_message(
            "improper-value-assert",
            args=(inferred.name, replacement_str),
            node=node)

    def _check_improper_assert(self, node, inferred):
        if not (
            isinstance(inferred, astroid.BoundMethod)
            and node.args
        ):
            return

        if self._is_assert_bool(node, inferred):
            self._add_assert_message(node, inferred, "assertTrue")
            return
        if self._is_assert_compare(node, inferred):
            assert_arg = node.args[0]
            assert_ops = assert_arg.ops[0]
            if self._is_compare_to_none(assert_ops):
                self._add_assert_message(
                    node, inferred, "assertIsNone or assertIsNotNone")
            elif assert_ops[0] in self.replacements:
                self._add_assert_message(
                    node, inferred, self.replacements[assert_ops[0]])
            return
        if self._is_assert_instance(node, inferred):
            self._add_assert_message(
                node, inferred, "assertIsInstance or assertNotIsInstance")


def register(linter):
    linter.register_checker(ValueAssertChecker(linter))
