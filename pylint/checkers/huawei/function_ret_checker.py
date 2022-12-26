# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

from astroid import nodes

from pylint.checkers import BaseChecker
from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker

class FunctionRetChecker(BaseChecker):
    __implements__ = IAstroidChecker
    name = 'function-ret'
    priority = -1
    
    msgs = {
        'H3407': (
            'The return value and exception of the function are not processed',
            'function-ret',
            'Correctly handle the return value and exception of the function.'
        ),
    }
    
    options = (
            (
                "function-ret-list",
                {
                    "default": "",
                    "type": "string"
                }
            ),
            (
                "check-function-ret",
                {
                    "default": True,
                    "type": "yn",
                    "metavar": "<y or n>",
                    "help": "This flag controls whether the return value of functions should be checked"
                },
            ),
        )

    def __init__(self, linter=None):
        super(FunctionRetChecker, self).__init__(linter)
        # configuration function list has return value 
        self.default_function_ret_list = []
        # called function return value list
        self.ret_list = {}
        # error list which return value of called function not processed
        self.err_list = []
        #function list has implicit return value
        self.function_ret_list = []
        
    @classmethod
    def check_func_ret(cls, node):
        '''
            check function implicit has return statement
        '''
        for child in node.get_children():
            # embed child function is skipped
            if isinstance(child, nodes.FunctionDef):
                continue
            # return statement should have at least one value
            if isinstance(child, nodes.Return) and child.value is not None:
                return True
            if cls.check_func_ret(child):
                return True
        return False
        
    @classmethod
    def check_try_exception_block(cls, node):
        '''
            called function in try exception block
        '''
        if node is None or isinstance(node, (nodes.Module, nodes.FunctionDef)):
            return False
        
        if node.parent is not None and isinstance(node.parent, nodes.TryExcept):
            return True

        return cls.check_try_exception_block(node.parent)

    def open(self):
        super().open()
        if self.config.function_ret_list.strip() != '':
            self.default_function_ret_list.extend(self.config.function_ret_list.strip().split(','))
            
    def check_call_args(self, args):
        '''
            check called function args is return value of function.
            when return value of function is an argument of another function, will not pop error.
        '''
        for arg in args:
            arg_name = arg.as_string()
            if arg_name in self.ret_list:
                self.ret_list.pop(arg_name)

    @check_messages("function-ret")
    def visit_call(self, node):
        if node.args:
            self.check_call_args(node.args)
        if node.func.as_string() not in (self.default_function_ret_list + self.function_ret_list):
            return
        if isinstance(node.parent, nodes.Expr) and self.config.check_function_ret:
            if self.check_try_exception_block(node.parent):
                return
            self.err_list.append(node)
        elif isinstance(node.parent, nodes.Assign):
            self.check_assign_ret(node.parent)
        
    def check_assign_ret(self, node):
        
        def is_remit_ret(target_name):
            '''
                remit global, _, and class object variables
            '''
            globs = node.root().globals
            if target_name == '_' or target_name in globs or target_name.find(".") != -1:
                return True
            return False
    
        target = node.targets[0]
        if isinstance(target, nodes.Tuple):
            for elt in target.elts:
                name = elt.as_string()
                if is_remit_ret(name):
                    continue
                self.ret_list[name] = elt
        elif isinstance(target, nodes.Subscript):
            return
        else:
            name = target.as_string()
            if is_remit_ret(name):
                return
            self.ret_list[name] = target
    
    @check_messages("function-ret")    
    def visit_name(self, node):
        name = node.as_string()
        if name in self.ret_list:
            self.ret_list.pop(name)

    def visit_functiondef(self, node):
        has_ret = self.check_func_ret(node)
        if has_ret:
            args = node.args.args
            name = node.name
            if args and isinstance(node.parent, nodes.ClassDef):
                if args[0].as_string() == 'self':
                    name = 'self.' + name
                elif args[0].as_string() == 'cls':
                    name = 'cls.' + name
            self.function_ret_list.append(name)
            
    def leave_functiondef(self, node):
        # embed child function
        if isinstance(node.parent, nodes.FunctionDef):
            return
        for err in self.ret_list.values():
            self.err_list.append(err)
        self.ret_list = {}

    def leave_module(self, _):
        for err in self.ret_list.values():
            self.err_list.append(err)
        for err in self.err_list:
            self.add_message('function-ret', node=err)
        self.ret_list = {}
        self.err_list = []
        self.function_ret_list = []

def register(linter):
    linter.register_checker(FunctionRetChecker(linter))
