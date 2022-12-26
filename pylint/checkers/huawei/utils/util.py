# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

import astroid
from typing import Set, Optional
from astroid import nodes
from pylint.checkers.utils import is_none

def get_docstring_line(filename):
    docstring_lineno = 0
    try:
        with open(filename, "r", encoding='utf-8') as lines:
            for line in lines:
                docstring_lineno += 1
                line = line.strip()
                if line.startswith("\'\'\'") or line.startswith('\"\"\"'):
                    return docstring_lineno
    except (IOError, UnicodeDecodeError):
        return None
    return None


def check_if_main(statement):
    '''
    Return True if statement is if __name__=="__main__"

    :param statement: Node considered
    :type node: astroid.Node
    :return: True if statement is if __name__=="__main__". False otherwise.
    :rtype: bool
    '''
    is_main_statement = False
    if isinstance(statement, astroid.If) and isinstance(statement.test, astroid.Compare):
        is_main_statement = isinstance(statement.test.left, astroid.Name) and \
                                    statement.test.left.name == "__name__" and \
                        isinstance(statement.test.ops[0][1], astroid.Const) and \
                                    statement.test.ops[0][1].value == "__main__"
    return is_main_statement


def get_attribute_name(node):
    '''
    Return node attribute name,if node is Name type,return node name

    :param node: Node considered
    :type node: astroid.Node
    :return: node attribute name,node type is only Name and Attribute type.
    :rtype: str
    '''
    if isinstance(node, astroid.Name):
        return node.name
    elif isinstance(node, astroid.Attribute):
        return get_attribute_name(node.expr) + "." + node.attrname
    return ''
    

def node_type(node: nodes.NodeNG) -> Optional[type]:
    """Return the inferred type for `node`.

    If there is more than one possible type, or if inferred type is Uninferable or None,
    return None
    """
    # check there is only one possible type for the assign node. Else we
    # don't handle it for now
    types: Set[type] = set()
    try:
        for var_type in node.infer():
            if var_type == astroid.Uninferable or is_none(var_type):
                continue
            types.add(type(var_type))
            if len(types) > 1:
                return None
    except astroid.InferenceError:
        return None
    return types.pop() if types else None
