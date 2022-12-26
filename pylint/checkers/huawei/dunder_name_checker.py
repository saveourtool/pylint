# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

from pylint.checkers import BaseChecker
from pylint.checkers.utils import (
    _SPECIAL_METHODS_PARAMS,
    check_messages,
    NEXT_METHOD,
    GETITEM_METHOD,
    CLASS_GETITEM_METHOD,
    SETITEM_METHOD,
    DELITEM_METHOD,
)
from pylint.interfaces import IAstroidChecker


class DunderNameChecker(BaseChecker):
    __implements__ = IAstroidChecker
    name = 'dunder-name'
    priority = -1

    msgs = {
        "H2105": (  # python 3.0 standard 2.1.1 G.NAM.05
            "Do not name generic objects with names that start "
            "and end with double underscores.",
            "not-use-double-underlines",
            "Do not name generic objects with names that start "
            "and end with double underscores.",
        )
    }

    options = (
        (
            "magic-functions",
            {
                "default": [],
                "type": "csv",
                "metavar": "",
                "help": "",
            },
        ),
        (
            "magic-variables",
            {
                "default": [],
                "type": "csv",
                "metavar": "",
                "help": "",
            },
        ),
    )

    def __init__(self, linter=None):
        super(DunderNameChecker, self).__init__(linter)
        self.default_magic_function = None
        self.default_magic_variable = None

    def open(self):
        super().open()
        if not self.default_magic_function:
            self.default_magic_function = [name
                                           for methods in _SPECIAL_METHODS_PARAMS.values()
                                           for name in methods]
            self.default_magic_function += ['__sizeof__', '__hex__', '__oct__', '__long__',
                                            '__subclass__', '__slots__', '__version__', '__idiv__',
                                            '__ifloordiv____missing__', '__post_init__', NEXT_METHOD,
                                            GETITEM_METHOD, CLASS_GETITEM_METHOD, SETITEM_METHOD, DELITEM_METHOD]

        if not self.default_magic_variable:
            self.default_magic_variable = \
                self.default_magic_function + [
                    '__revision__', '__pkginfo__', '__author__', '__email__',
                    '__copyright__', '__metaclass__', '__dict__',
                    '__implements__', '__docformat__', '__all__']

    @check_messages("dunder-name")
    def visit_functiondef(self, node):
        if node.name.startswith("__") and node.name.endswith("__"):
            magic_function = getattr(self.config, 'magic_functions')
            if node.name not in self.default_magic_function + magic_function:
                self.add_message(
                    "not-use-double-underlines", node=node
                )

    @check_messages("dunder-name")
    def visit_assignname(self, node):
        if node.name.startswith("__") and node.name.endswith("__"):
            magic_variable = getattr(self.config, 'magic_variables')
            if node.name not in self.default_magic_variable + magic_variable:
                self.add_message("not-use-double-underlines", node=node)


def register(linter):
    linter.register_checker(DunderNameChecker(linter))
