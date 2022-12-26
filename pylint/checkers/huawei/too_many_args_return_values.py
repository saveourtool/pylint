# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

import astroid

from pylint.checkers import BaseChecker
from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker

MSGS = {
    "H3403": (
        "Too many arguments (%d/%d)",
        "huawei-too-many-arguments",
        "Used when a function or method takes too many arguments.",
    ),
    "H3405": (
        "Too many return values in a return statement (%d/%d)",
        "too-many-return-values",
        "Used when a return statement contains too many return values.",
    ),
}

IGNORE_METHOD = ['__init__', '__new__', '__prepare__', '__init_subclass__']


class MisdesignHuaweiChecker(BaseChecker):
    """checks for sign of poor/misdesign:
    * number of methods, attributes, local variables...
    * size, complexity of functions, methods
    """

    __implements__ = (IAstroidChecker,)

    # configuration section name
    name = "design"
    # messages
    msgs = MSGS
    priority = -2
    # configuration options
    options = (
        (
            "max-args-huawei",
            {
                "default": 5,
                "type": "int",
                "metavar": "<int>",
                "help": "Maximum number of arguments for function / method.",
            },
        ),
        (
            "max-return-values-huawei",
            {
                "default": 3,
                "type": "int",
                "metavar": "<int>",
                "help": "Maximum number of return values for a return / "
                        " statement/ "
            },
        ),
    )

    def __init__(self, linter=None):
        super().__init__(linter)
        self._returns = None

    def open(self):
        """initialize visit variables"""
        self._returns = []

    @check_messages(
        "huawei-too-many-arguments",
        "too-many-return-values",
    )
    def visit_functiondef(self, node):
        """Check whether this function has too many arguments.
        """
        # init branch and returns counters
        self._returns.append(0)
        # check number of arguments
        if node.name in IGNORE_METHOD:
            return
        args = node.args.args
        if args is not None:
            argnum = len(args) - self.ignore_argument_cnt(node)
            if argnum > self.config.max_args_huawei:
                self.add_message(
                    "huawei-too-many-arguments",
                    node=node,
                    args=(argnum, self.config.max_args_huawei),
                )

    visit_asyncfunctiondef = visit_functiondef

    @staticmethod
    def ignore_argument_cnt(node: astroid.FunctionDef):
        if not node.is_method():
            return 0
        if node.type == 'staticmethod':
            return 0
        return 1

    @check_messages("too-many-return-values")
    def visit_return(self, node):
        """count number of returns and the number of return values in a return statement
        """
        if not self._returns:
            return  # return outside function, reported by the base checker
        self._returns[-1] += 1
        if isinstance(node.value, astroid.Tuple) and \
                isinstance(node.value.elts, list) and \
                len(node.value.elts) > self.config.max_return_values_huawei:
            self.add_message(
                "too-many-return-values",
                node=node,
                args=(len(node.value.elts), self.config.max_return_values_huawei)
            )


def register(linter):
    """required method to auto register this checker """
    linter.register_checker(MisdesignHuaweiChecker(linter))
