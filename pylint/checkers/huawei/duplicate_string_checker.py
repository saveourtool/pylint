# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

from astroid import nodes
from pylint.checkers import BaseChecker
from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker


class DuplicateStringChecker(BaseChecker):
    __implements__ = IAstroidChecker
    name = 'duplicate-string'
    priority = -1
    msgs = {
        "H3103": (  # python 3.0 standard 3.1 G.TYP.03
            "Duplicate string literal '%s' at line %s.",
            "duplicate-string",
            "Repeated string literals make the reconstruction process error"
            " prone and result in scattershot modifications. You are advised"
            " to extract repeated string literals as constant strings",
        ),
    }

    def __init__(self, linter=None):
        super(DuplicateStringChecker, self).__init__(linter)
        self.string_dicts = []
        self.current_func = []
        self.in_joinedstr = False
        self.duplicate_limit = 3
        self.ignore_length_limit = 1

    @check_messages("duplicate-string")
    def leave_functiondef(self, node):
        if not self.string_dicts:
            return
        cur_dict = self.string_dicts[-1]
        for str_const in cur_dict:
            lines = cur_dict[str_const]
            if len(lines) >= self.duplicate_limit:
                self.add_message("duplicate-string",
                                 line=node.lineno, node=node, args=(str_const, lines))

        self.string_dicts.pop(-1)
        self.current_func.pop(-1)

    @check_messages("duplicate-string")
    def visit_functiondef(self, node):
        self.string_dicts.append({})
        self.current_func.append(node)

    @check_messages("duplicate-string")
    def visit_const(self, node):
        if self.should_skip_const(node):
            return
        cur_dict = self.string_dicts[-1]
        cur_dict.setdefault(node.value, []).append(node.lineno)

    def should_skip_const(self, node: nodes.Const):
        return not self.string_dicts \
            or not self.current_func \
            or not type(node.value) is str \
            or len(node.value) <= self.ignore_length_limit \
            or self.in_joinedstr

    @check_messages("duplicate-string")
    def visit_joinedstr(self, node: nodes.JoinedStr):
        self.in_joinedstr = True

    @check_messages("duplicate-string")
    def leave_joinedstr(self, node: nodes.JoinedStr):
        self.in_joinedstr = False


def register(linter):
    linter.register_checker(DuplicateStringChecker(linter))
