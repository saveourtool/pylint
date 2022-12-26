# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

from pylint.checkers import BaseChecker
from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker

MSGS = {
    "W1802": (
        "Avoid using '__import__' functions",
        "avoid-import-method",
        "Avoid using '__import__' functions"
    )
}


class ProgrammingPracticesChecker(BaseChecker):
    __implements__ = (IAstroidChecker,)

    # configuration section name
    name = "newstyle"
    # messages
    msgs = MSGS
    priority = -2
    # configuration options
    options = ()


    def __init__(self, linter=None):
        super(ProgrammingPracticesChecker, self).__init__(linter)


    @check_messages("avoid-import-method")
    def visit_call(self, node):
        if hasattr(node.func, 'name') and node.func.name == '__import__':
            self.add_message("avoid-import-method", node=node)

def register(linter):
    """required method to auto register this checker """
    linter.register_checker(ProgrammingPracticesChecker(linter))
