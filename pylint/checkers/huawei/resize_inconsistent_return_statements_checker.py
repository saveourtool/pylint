# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

"""针对规范，优化覆盖面 G.CTL.01 同一个函数所有分支的返回值类型和个数保持一致
"""
import typing

import astroid
from astroid import nodes

from pylint.checkers import BaseChecker
from pylint.checkers.utils import check_messages
from pylint.checkers import utils
from pylint.interfaces import IAstroidChecker


# 代码内容大部分出自 ...\codecheck-pylint13\pylint\checkers\refactoring\refactoring_checker.py 继承自规则R1710
class ResizeInconsistentReturnStatementsChecker(BaseChecker):
    __implements__ = IAstroidChecker
    name = 'resize-inconsistent-return-statements'
    priority = -1

    msgs = {
        'H0301': (
            'Return statements should have same number and type of return value',
            'resize-inconsistent-return-statements',
            'the return value must be unified as implicit or explicit, and must be the same number and type'
        ),
        'H0311': (
            '%s',
            'implicitly-return-none',
            'return None that should be displayed here'
        ),
    }

    options = (
        (
            "resize_inconsistent_return_statements",
            {
                "default": ("sys.exit", "argparse.parse_error"),
                "type": "csv",
                "help": "Complete name of functions that never returns. When checking "
                        "for inconsistent-return-statements if a never returning function is "
                        "called then it will be considered as an explicit return statement "
                        "and no message will be printed.",
            },

        ),
    )

    def __init__(self, linter=None):
        super().__init__(linter)
        self._return_nodes = {}
        self._resize_inconsistent_return_statements = None
        self.warning_list_of_strong_consistency = []
        self.return_nothing = []
        self.max_lens = 0  # 所有返回值最大个数

    def _check_return_len(self, explicit_returns) -> bool:
        default_type_len = 1
        if len(explicit_returns) == default_type_len:
            self.max_lens = len(explicit_returns[0].value.elts) \
                if isinstance(explicit_returns[0].value, nodes.Tuple) else 1
            return False
        base_type = set()
        exit_call_name = set()
        base_return_type = (nodes.Const, nodes.Dict, nodes.Set, nodes.List)
        default_type = None
        none_return_flag = False
        for i in explicit_returns:
            g_first = i.value.infer()
            try:
                f = next(g_first)
            except Exception as e:
                f = None
            if f and isinstance(f, base_return_type):
                if isinstance(f, nodes.Const) and f.value is None:
                    if default_type and self.max_lens == default_type_len:
                        self.add_message("implicitly-return-none", node=i,
                                         args='Do not use None instead of the basic data type.')
                        return True
                    none_return_flag = True
                elif none_return_flag and self.max_lens <= default_type_len:
                    self.add_message("implicitly-return-none", node=i,
                                     args='Do not use None instead of the basic data type.')
                    return True  # 当出现集合字典构成方法的时候，需要确保其余返回值为1且类型不一致.或者存在单一的None返回值
                elif default_type and self.max_lens <= default_type_len and default_type != type(f):
                    self.warning_list_of_strong_consistency.append(i)
                    return True  # 当出现集合字典构成方法的时候，需要确保其余返回值为1且类型不一致.或者存在单一的None返回值
                elif self.max_lens <= default_type_len and not default_type:
                    # 当初单个非容器类型属于内置类型的时候需要对他的类型进行判断处理
                    default_type = type(f)
            if isinstance(i.value, nodes.Tuple):
                call_name_tuple = set(
                    [elt.func.as_string() for elt in filter(lambda x: isinstance(x, nodes.Call), i.value.elts)])
                exit_call_name = exit_call_name.union(call_name_tuple)
                if len(call_name_tuple.union(base_type)) != len(call_name_tuple) + len(base_type):
                    self.warning_list_of_strong_consistency.append(i)
                    return True
                tmp_lens = len(i.value.elts)
                if not self.max_lens:
                    self.max_lens = tmp_lens
                    continue
                elif tmp_lens == self.max_lens:
                    continue
                self.warning_list_of_strong_consistency.append(i)
                return True
            elif isinstance(i.value, nodes.Call):
                call_name = i.value.func.as_string()
                if call_name not in base_type:
                    base_type.add(call_name)
                if call_name in exit_call_name:
                    self.warning_list_of_strong_consistency.append(i)
                    return True
            if self.max_lens <= default_type_len:
                self.max_lens = default_type_len
                continue
            elif self.max_lens > default_type_len:
                self.warning_list_of_strong_consistency.append(i)
                return True
        return False

    @staticmethod
    def _has_return_in_siblings(node: nodes.NodeNG) -> bool:
        """Returns True if there is at least one return in the node's siblings."""
        next_sibling = node.next_sibling()
        while next_sibling:
            if isinstance(next_sibling, nodes.Return):
                return True
            next_sibling = next_sibling.next_sibling()
        return False

    def open(self):
        # do this in open since config not fully initialized in __init__
        self._resize_inconsistent_return_statements = set(self.config.resize_inconsistent_return_statements)

    @check_messages("resize-inconsistent-return-statements",
                    "implicitly-return-none", )
    def leave_functiondef(self, node: nodes.FunctionDef) -> None:
        self._check_consistent_returns(node)
        self._return_nodes[node.name] = []
        self.return_nothing = []
        self.max_lens = 0

    @check_messages("resize-inconsistent-return-statements",
                    "implicitly-return-none", )
    def visit_functiondef(self, node: nodes.FunctionDef) -> None:
        self._return_nodes[node.name] = list(
            node.nodes_of_class(nodes.Return, skip_klass=nodes.FunctionDef)
        )

    def _add_msg_report(self, type_str: str, msg_list: typing.List, args=None):
        for i in msg_list:
            self.add_message(type_str, node=i, args=args)
        if type_str == "resize-inconsistent-return-statements":
            self.warning_list_of_strong_consistency = []

    def _check_consistent_returns(self, node: nodes.FunctionDef) -> None:
        """Check that all return statements inside a function are consistent.

        Return statements are consistent if:
            - all returns are explicit and if there is no implicit return;
            - all returns are empty and if there is, possibly, an implicit return.

        Args:
            node (nodes.FunctionDef): the function holding the return statements.

        """
        # explicit return statements are those with a not None value
        explicit_returns = [
            _node for _node in self._return_nodes[node.name] if _node.value is not None
        ]
        if not explicit_returns:
            return
        im_return, real_return = list(
            filter(lambda x: x.value is None, self._return_nodes[node.name])
        ), list(
            filter(lambda x: x.value is not None, self._return_nodes[node.name])
        )  # im_return隐式返回列表， real_return显示返回列表
        real_count = len(real_return)
        if self._check_return_len(explicit_returns):
            self._add_msg_report("resize-inconsistent-return-statements", self.warning_list_of_strong_consistency)
            return
        if not self._is_node_return_ended(node):
            if self.max_lens <= 1:
                if im_return:
                    self._add_msg_report("implicitly-return-none", im_return,
                                         args='It is recommended to avoid implicitly returning None.')
                else:
                    self.add_message("implicitly-return-none", node=node,
                                     args='It is recommended to avoid implicitly returning None.')
            else:
                self.add_message("resize-inconsistent-return-statements", node=node)
            return
        if len(explicit_returns) == len(
                self._return_nodes[node.name]
        ) and self._is_node_return_ended(node):
            return
        elif real_count == len(explicit_returns):
            if list(filter(lambda x: isinstance(x.value, nodes.Tuple), real_return)):
                self.add_message("resize-inconsistent-return-statements", node=node)
            else:
                self._add_msg_report("implicitly-return-none", im_return,
                                     args='It is recommended to avoid implicitly returning None.')
            return
        self.add_message("resize-inconsistent-return-statements", node=node)

    def _is_node_return_ended(self, node: nodes.NodeNG) -> bool:
        """Check if the node ends with an explicit return statement.

        Args:
            node (nodes.NodeNG): node to be checked.

        Returns:
            bool: True if the node ends with an explicit statement, False otherwise.

        """
        # Recursion base case
        if isinstance(node, nodes.Return):
            return True
        if isinstance(node, nodes.Call):
            try:
                funcdef_node = node.func.inferred()[0]
                if self._is_function_def_never_returning(funcdef_node):
                    return True
            except astroid.InferenceError:
                pass
        # Avoid the check inside while loop as we don't know
        # if they will be completed
        if isinstance(node, nodes.While):
            return True
        if isinstance(node, nodes.Raise):
            return self._is_raise_node_return_ended(node)
        if isinstance(node, nodes.If):
            return self._is_if_node_return_ended(node)
        if isinstance(node, nodes.TryExcept):
            handlers = {
                _child
                for _child in node.get_children()
                if isinstance(_child, nodes.ExceptHandler)
            }
            all_but_handler = set(node.get_children()) - handlers
            return any(
                self._is_node_return_ended(_child) for _child in all_but_handler
            ) and all(self._is_node_return_ended(_child) for _child in handlers)
        if (
                isinstance(node, nodes.Assert)
                and isinstance(node.test, nodes.Const)
                and not node.test.value
        ):
            # consider assert False as a return node
            return True
        # recurses on the children of the node
        return any(self._is_node_return_ended(_child) for _child in node.get_children())

    def _is_function_def_never_returning(self, node: nodes.FunctionDef) -> bool:
        """Return True if the function never returns, False otherwise.

        Args:
            node (nodes.FunctionDef): function definition node to be analyzed.

        Returns:
            bool: True if the function never returns, False otherwise.
        """
        if isinstance(node, nodes.FunctionDef) and node.returns:
            return (
                    isinstance(node.returns, nodes.Attribute)
                    and node.returns.attrname == "NoReturn"
                    or isinstance(node.returns, nodes.Name)
                    and node.returns.name == "NoReturn"
            )
        try:
            return node.qname() in self._resize_inconsistent_return_statements
        except TypeError:
            return False

    def _is_raise_node_return_ended(self, node: nodes.Raise) -> bool:
        """Check if the Raise node ends with an explicit return statement.

        Args:
            node (nodes.Raise): Raise node to be checked.

        Returns:
            bool: True if the node ends with an explicit statement, False otherwise.
        """
        # a Raise statement doesn't need to end with a return statement
        # but if the exception raised is handled, then the handler has to
        # ends with a return statement
        if not node.exc:
            # Ignore bare raises
            return True
        if not utils.is_node_inside_try_except(node):
            # If the raise statement is not inside a try/except statement
            # then the exception is raised and cannot be caught. No need
            # to infer it.
            return True
        exc = utils.safe_infer(node.exc)
        if exc is None or exc is astroid.Uninferable or not hasattr(exc, "pytype"):
            return False
        exc_name = exc.pytype().split(".")[-1]
        handlers = utils.get_exception_handlers(node, exc_name)
        handlers = list(handlers) if handlers is not None else []
        if handlers:
            # among all the handlers handling the exception at least one
            # must end with a return statement
            return any(self._is_node_return_ended(_handler) for _handler in handlers)
        # if no handlers handle the exception then it's ok
        return True

    def _is_if_node_return_ended(self, node: nodes.If) -> bool:
        """Check if the If node ends with an explicit return statement.

        Args:
            node (nodes.If): If node to be checked.

        Returns:
            bool: True if the node ends with an explicit statement, False otherwise.
        """
        # Do not check if inner function definition are return ended.
        is_if_returning = any(
            self._is_node_return_ended(_ifn)
            for _ifn in node.body
            if not isinstance(_ifn, nodes.FunctionDef)
        )
        if not node.orelse:
            # If there is not orelse part then the if statement is returning if :
            # - there is at least one return statement in its siblings;
            # - the if body is itself returning.
            if not self._has_return_in_siblings(node):
                return False
            return is_if_returning
        # If there is an orelse part then both if body and orelse part should return.
        is_orelse_returning = any(
            self._is_node_return_ended(_ore)
            for _ore in node.orelse
            if not isinstance(_ore, nodes.FunctionDef)
        )
        return is_if_returning and is_orelse_returning


def register(linter):
    linter.register_checker(ResizeInconsistentReturnStatementsChecker(linter))
