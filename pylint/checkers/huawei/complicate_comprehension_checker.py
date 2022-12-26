# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

from pylint.checkers import BaseChecker
from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker


class ComplicateComprehensionChecker(BaseChecker):
    __implements__ = IAstroidChecker
    name = 'complicate-comprehension'
    priority = -1
    COMPLICATE_COMPREHENSION = 'complicate-comprehension'
    # the maximum number of clauses allowed, including for-clauses and if-clauses.
    MAX_CLAUSES = 2
    msgs = {
        'W1803': (
            'Do not use more than two clauses or clauses that has more than one line.',
            COMPLICATE_COMPREHENSION,
            'Comprehension and generator should use no more than two for/if clauses, and each for/If clause should be in one line.'
        ),
    }

    def __init__(self, linter=None):
        super(ComplicateComprehensionChecker, self).__init__(linter)

    @check_messages("complicate-comprehension")
    def visit_listcomp(self, node):
        self.check_comprehensions(node)

    @check_messages("complicate-comprehension")
    def visit_dictcomp(self, node):
        self.check_comprehensions(node)

    @check_messages("complicate-comprehension")
    def visit_setcomp(self, node):
        self.check_comprehensions(node)

    @check_messages("complicate-comprehension")
    def visit_generatorexp(self, node):
        self.check_comprehensions(node)

    def check_single_line_if(self, ifs):
        for node in ifs:
            if(node.fromlineno != node.tolineno):
                self.add_message(self.COMPLICATE_COMPREHENSION, node=node)

    def check_single_line_for(self, comp):
        if(comp.target.fromlineno != comp.iter.tolineno):
            self.add_message(self.COMPLICATE_COMPREHENSION, node=comp.target)

    def check_single_comprehension(self, comp):
        self.check_single_line_if(comp.ifs)
        self.check_single_line_for(comp)
        # return the total number of clauses,
        # which is the number of if-clauses plus one for-clause.
        return len(comp.ifs) + 1

    def check_comprehensions(self, node):
        comprehension_count = 0
        for child in node.generators:
            comprehension_count += self.check_single_comprehension(child)
        if comprehension_count > self.MAX_CLAUSES:
            self.add_message(self.COMPLICATE_COMPREHENSION, node=node)


def register(linter):
    linter.register_checker(ComplicateComprehensionChecker(linter))
