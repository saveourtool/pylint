# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

import builtins
from inspect import getmembers
import importlib

from astroid import Tuple

from pylint.checkers import BaseChecker
from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker
import pylint.checkers.huawei.utils.util as huawei_util


class CatchSameException(BaseChecker):
    __implements__ = IAstroidChecker
    name = 'catch-same-exception'
    priority = -1
    msgs = {
        "W0718": (
            "%s",
            "not-get-same-exception",
            "do not capture both parent and child exceptions and "
            "do not capture the same exception repeatedly.",
        ),
    }

    def __init__(self, linter=None):
        super(CatchSameException, self).__init__(linter)

    @staticmethod
    def exception_relationship(son):
        '''
        Return exception parent class list

        :param son: exception class name
        :type son: str
        :return: exception class mro list.
        :rtype: list
        '''
        def predicate(obj):
            return isinstance(obj, type) and issubclass(obj, BaseException)

        # process Attribute Node
        if son.find('.') != -1:
            strs = son.split('.')
            class_name = strs[-1]
            mods = strs[0:-1]
            son = class_name
            try:
                # import exception class module and get module members
                module_obj = importlib.import_module('.'.join(mods))
            except Exception:
                members = []
            else:
                members = getmembers(module_obj, predicate)
        # process Name Node
        else:
            members = getmembers(builtins, predicate)

        for (exception_name, exception_class) in members:
            if exception_name != son:
                continue
            exception_relationship = []
            for parents in exception_class.__mro__:
                if parents.__module__ == 'builtins':
                    # builtin exception class
                    exception_relationship.append(parents.__name__)
                else:
                    # custom exception class 
                    exception_relationship.append(parents.__module__ + "." + parents.__name__)
            return exception_relationship[1:-1]
        return []

    @classmethod     
    def get_exception_name(cls, node):
        '''
        Return exception node name

        :param node: Node considered
        :type node: astroid.Node
        :return: exception node name,node type is only Name and Attribute type.
        :rtype: str
        '''
        return huawei_util.get_attribute_name(node)

    @check_messages("not-get-same-exception")
    def visit_excepthandler(self, node):
        same_exception_set = set()
        parents_set = set()
        same_msg = "Do not capture the same exception repeatedly."
        parent_child_msg = "Do not capture both parent and child exceptions."
        if node.type and type(node.type) is Tuple:
            for exception_item in node.type.elts:
                exception_name = self.get_exception_name(exception_item)
                if exception_name not in same_exception_set:
                    exceptions = self.exception_relationship(exception_name)
                    if exceptions:
                        for i in exceptions:
                            parents_set.add(i)
                    same_exception_set.add(exception_name)
                else:
                    self.add_message("not-get-same-exception", node=node, args=same_msg)
            for exception_item in node.type.elts:
                exception_name = self.get_exception_name(exception_item)
                if exception_name in parents_set:
                    self.add_message("not-get-same-exception", node=node, args=parent_child_msg)


def register(linter):
    linter.register_checker(CatchSameException(linter))
