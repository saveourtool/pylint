# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

import os
import sys

from pylint.checkers import BaseChecker
from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker
import pylint.checkers.huawei.utils.util as huawei_util


class RelativeImportChecker(BaseChecker):
    __implements__ = IAstroidChecker
    name = 'relative-import'
    priority = -1

    msgs = {
        'H3901': (
            '%s',
            'relative-import',
            'Relative import found in main module'
        ),
    }

    def __init__(self, linter=None):
        super().__init__(linter)
        #relative import packages in module
        self.relatives = []
        #absolute import packages in module
        self.absolutes = []
        self._is_main_module = False
        self._module = None

    @staticmethod
    def get_pkg_path(path):
        '''
        get import pkg full path through sys path
     
        :param path: module full path
        :type node: str
        :return: module relative path through sys path
        :rtype: str
        '''
        pkg_normal_path = os.path.normpath(path)
        ref_sys_path = None
        for syspath in sys.path:
            normal_syspath = os.path.normpath(syspath)
            if pkg_normal_path.find(normal_syspath) != -1:
                if ref_sys_path is None or normal_syspath.find(ref_sys_path) != -1:
                    ref_sys_path = normal_syspath
        
        if ref_sys_path is not None:
            relative_path = pkg_normal_path.replace(ref_sys_path, '').strip(os.sep)
            pkg_relative_path = relative_path.replace(os.sep, '.')
            return pkg_relative_path
        return pkg_normal_path
        
    @staticmethod
    def check_main_module(module):
        '''
        Return True if module is main

        :param module: Node considered
        :type node: astroid.Node
        :return: True if module is main. False otherwise.
        :rtype: bool
        '''
        for statement in module.body:
            if huawei_util.check_if_main(statement):
                return True
        return False
        
    @check_messages("relative-import")
    def visit_module(self, node):
        self._module = node
        self._is_main_module = self.check_main_module(self._module)

    @check_messages("relative-import")
    def visit_importfrom(self, node):
        self.check_relative_import(node, self._is_main_module)
        self.get_from_imports(self._module, node)

    @check_messages("relative-import")
    def visit_import(self, node):
        self.get_imports(node)

    def leave_module(self, node):
        self.pop_relative_import_errors()
        self._module = None
        self.relatives = []
        self.absolutes = []

    def check_relative_import(self, node, is_main_module):
        if is_main_module and node.level is not None and node.level > 0:
            self.add_message('relative-import', node=node, args='Relative import found in executable script')

    def get_from_imports(self, module, statement):
        '''
            get all from_imports
        '''
        module_path = module.file
        # relative imports
        if statement.level is not None and statement.level > 0:
            level = statement.level
            pkg_path = module_path
            while level > 0:
                pkg_path = os.path.dirname(pkg_path)
                level -= 1
            pkg_import_path = self.get_pkg_path(pkg_path).strip()
            # process from . import xx , or from .pkg import
            if statement.modname != '':
                if pkg_import_path != '':
                    pkg_import_path += "."
                pkg_import_path += statement.modname
            if pkg_import_path != '':
                self.relatives.append([statement, pkg_import_path])
        # absolute imports
        elif statement.level is None:
            self.absolutes.append((statement, [statement.modname]))

    def get_imports(self, statement):
        '''
            get all imports
        '''
        # absolute imports
        self.absolutes.append((statement, [name[0] for name in statement.names]))

    def pop_relative_import_errors(self):
        '''
            check both absolute and relative paths import same package and pop errors
        '''
        source_msg = 'Use both absolute and relative paths import same package(%s).Relative:(line %d)'
        for statement, names in self.absolutes:
            for node, relative_import_path in self.relatives:
                for name in names:
                    if name.find(relative_import_path) == -1:
                        continue
                    msg = source_msg % (relative_import_path, node.lineno)
                    self.add_message('relative-import', node=statement, args=msg)


def register(linter):
    linter.register_checker(RelativeImportChecker(linter))
