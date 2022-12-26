# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

import re

import astroid

# 是否使用前缀进行匹配
is_prefix = 'True'

# 获取python函数名，函数开始行，函数结束行
def get_func_info(node):
    func_infos = []
    for fileNode in node.body:
        if type(fileNode) is astroid.FunctionDef:
            func_info = [fileNode.name, fileNode.fromlineno, fileNode.tolineno]
            func_infos.append(func_info)
            continue
        if type(fileNode) is astroid.ClassDef:
            for name in get_func_info(fileNode):
                func_infos.append(name)
    return func_infos

# 获取python函数名
def get_func_names(node):
    func_names = []
    for fileNode in node.body:
        if type(fileNode) is astroid.FunctionDef:
            func_names.append(fileNode.name)
            continue
        if type(fileNode) is astroid.ClassDef:
            for name in get_func_names(fileNode):
                func_names.append(name)
    return func_names

def get_func_from_config(func_str):
    if func_str.strip() == '':
        return ''
    return func_str.split(';')

def is_test_case(func_names, pre_func, do_test_func, clean_func):
    for func_name in func_names:
        if pre_func.match(func_name) or do_test_func.match(func_name) or clean_func.match(func_name):
            return True
    return False

def check_do_test_func_comment(code_lines, func_info):
    start_line = func_info[1]
    if check_comment(code_lines, start_line, 0):
        return True
    return check_comment_next(code_lines, start_line, 0)

def check_comment_next(code_lines, start_line, step):
    for code in code_lines:
        current_line = code.start[0]
        if current_line == start_line + 1:
            current_code = code.line.strip()
            if len(current_code) == 0 and step < 1:
                if check_comment_next(code_lines, current_line, step + 1):
                    return True
            if current_code.startswith('@'):
                if check_comment_next(code_lines, current_line, step):
                    return True
            if current_code.startswith('#') or current_code.startswith('"""') or current_code.startswith("'''"):
                return True
    return False


def check_comment(code_lines, start_line, step):
    for code in code_lines:
        current_line = code.start[0]
        if current_line == start_line - 1:
            current_code = code.line.strip()
            if len(current_code) == 0 and step < 1:
                if check_comment(code_lines, current_line, step + 1):
                    return True
            if current_code.startswith('@'):
                if check_comment(code_lines, current_line, step):
                    return True
            if current_code.startswith('#') or current_code.startswith('"""') or current_code.startswith("'''"):
                return True
    return False


def has_asset_func(node, do_test_funcs, assert_funcs, lines):
    for fileNode in node.body:
        if type(fileNode) is astroid.ClassDef:
            has_asset_func(fileNode, do_test_funcs, assert_funcs, lines)
        if type(fileNode) is not astroid.FunctionDef:
            continue
        if not do_test_funcs.match(fileNode.name):
            continue
        if not check_asset_body(fileNode, assert_funcs):
            lines.append(fileNode.fromlineno)


def check_asset_body(current, asset_funcs):
    current_node_body = []
    current_node_body.extend(current.body)
    if type(current) is astroid.If:
        current_node_body.extend(current.orelse)
    for code in current_node_body:
        if type(code) is astroid.If or type(code) is astroid.For or type(code) is astroid.While or type(
                code) is astroid.TryFinally or type(code) is astroid.With:
            if check_asset_body(code, asset_funcs):
                return True
        if type(code) is astroid.Assert:
            if asset_funcs.match('assert'):
                return True
        if type(code) is not astroid.Expr:
            continue
        if type(code.value) is astroid.Call:
            func = code.value.func
            func_expr = get_func_expr(func)
            if asset_funcs.match(func_expr):
                return True

    return False


def get_func_expr(func):
    if isinstance(func, astroid.Name):
        return func.name
    elif hasattr(func, "expr") and isinstance(func, astroid.Attribute):
        if not (isinstance(func.expr, astroid.Attribute) or isinstance(func.expr, astroid.Name)):
            return func.attrname
        ret = get_func_expr(func.expr)
        return ret + '.' + func.attrname
    else:
        return ''


def has_not_print_func(node, barred_func_do_test_func, lines, barred_func):
    for fileNode in node.body:
        if type(fileNode) is astroid.ClassDef:
            has_not_print_func(fileNode, barred_func_do_test_func, lines, barred_func)
            continue
        if type(fileNode) is not astroid.FunctionDef:
            continue
        if not barred_func_do_test_func.match(fileNode.name):
            continue
        check_print_func_body(fileNode, lines, barred_func)
    return lines

def check_print_func_body(code_bode, lines, target):
    current_node_body = []
    current_node_body.extend(code_bode.body)
    if type(code_bode) is astroid.If:
        current_node_body.extend(code_bode.orelse)
    for code in current_node_body:
        if type(code) is astroid.If or type(code) is astroid.For or type(code) is astroid.While or type(
                code) is astroid.TryFinally or type(code) is astroid.With:
            check_print_func_body(code, lines, target)
        if type(code) is not astroid.Expr:
            continue
        if type(code.value) is astroid.Call:
            func = code.value.func
            func_expr = get_func_expr(func)
            if target.match(func_expr):
                lines.append(func.lineno)
                continue


def has_storage_media(code_lines, start, end):
    lines = []
    for code in code_lines:
        if start <= code.start[0] <= end and code_has_excel(code.line.strip()):
            lines.append(code.start[0])
    return lines

def code_has_excel(code):
    if code.startswith('#'):
        return False
    return code.endswith('.xlsx') or code.endswith('.xls')

def is_do_test_func(do_test_funcs, current_func):
    for do_test_func in do_test_funcs:
        if current_func.startswith(do_test_func):
            return True
    return False


def check_false_pass(node, do_test_funcs, assert_funcs, lines):
    for fileNode in node.body:
        if type(fileNode) is astroid.ClassDef:
            check_false_pass(fileNode, do_test_funcs, assert_funcs, lines)
        if type(fileNode) is not astroid.FunctionDef:
            continue
        if not do_test_funcs.match(fileNode.name):
            continue

        for code in fileNode.body:
            if type(code) is astroid.If and type(code.test) is astroid.Const:
                if has_asset_func_in_body(code, assert_funcs):
                    lines.append(code.lineno)


def has_asset_func_in_body(code, assert_funcs):
    for expr in code.body:
        if type(expr) is astroid.For or type(expr) is astroid.While or type(expr) is astroid.TryFinally \
                or type(expr) is astroid.If or type(expr) is astroid.With:
            if has_asset_func_in_body(expr, assert_funcs):
                return True
        if type(expr) is astroid.Assert:
            if assert_funcs.match('assert'):
                return True
        if type(expr) is not astroid.Expr:
            continue
        var = expr.value
        if type(var) is astroid.Name:
            if assert_funcs.match(var.name):
                return True
            continue
        if type(var) is not astroid.Call:
            continue
        func = expr.value.func
        func_expr = get_func_expr(func)
        if assert_funcs.match(func_expr):
            return True

    return False
