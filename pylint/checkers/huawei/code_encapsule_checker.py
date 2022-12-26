# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

import astroid

from pylint.checkers import BaseChecker
from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker

import pylint.checkers.huawei.utils.util as huawei_util


class CodeEncapsuleChecker(BaseChecker):
    __implements__ = IAstroidChecker
    name = 'value-assert'
    priority = -1
    ignore_dunders = ['__all__', '__revision__', '__pkginfo__',
                      '__author__', '__email__', '__copyright__', '__docformat__']
    msgs = {
        "W0130": (
            "Function code should be encapsulated in a function or class. '%s'",
            "code-contained-in-function",
            "Function code should be encapsulated in a function or class.",
        ),
    }

    def __init__(self, linter=None):
        super(CodeEncapsuleChecker, self).__init__(linter)

    @check_messages("code-contained-in-function")
    def visit_module(self, node):
        line_list = list()
        for statement in node.body:
            if type(statement) is astroid.ClassDef:
                continue
            if type(statement) is astroid.FunctionDef:
                continue
            if type(statement) is astroid.Import:
                continue
            if type(statement) is astroid.ImportFrom:
                continue
            if huawei_util.check_if_main(statement):
                continue
            if type(statement) is astroid.Assign:
                if type(statement.targets[0]) is astroid.AssignName and \
                        statement.targets[0].name in self.ignore_dunders:
                    continue
            line_list.append(statement.lineno)
        if len(line_list) > 0:
            msg = "isolated code lines are: %s" % str(line_list)
            self.add_message("code-contained-in-function",
                             line=line_list[0], node=node, args=msg)


def register(linter):
    linter.register_checker(CodeEncapsuleChecker(linter))
