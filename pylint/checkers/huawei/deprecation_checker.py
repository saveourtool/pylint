# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

import sys
from typing import Any
from astroid import nodes

from pylint.checkers import BaseChecker
from pylint.checkers.utils import check_messages, get_import_name
from pylint.interfaces import IAstroidChecker
from pylint.checkers.stdlib import DEPRECATED_MODULES, DEPRECATED_CLASSES

class DeprecationChecker(BaseChecker):
    __implements__ = IAstroidChecker
    name = 'deprecation'
    priority = -1
    
    msgs: Any = {
        "H3111": (
            "Uses of a deprecated module %r",
            "huawei-deprecated-module",
            "A module marked as deprecated is imported.",
        ),
        "H3112": (
            "Using deprecated class %s of module %s",
            "huawei-deprecated-class",
            "The class is marked as deprecated and will be removed in the future.",
        ),
    }
    
    default_deprecated_modules = ()
    options = (
        (
            "huawei-deprecated-modules",
            {
                "default": default_deprecated_modules,
                "type": "csv",
                "metavar": "<modules>",
                "help": "Deprecated modules which should not be used,"
                " separated by a comma.",
            },
        ),
    )

    def __init__(self, linter=None):
        super().__init__(linter)
        self._deprecated_classes: Dict[str, Set[str]] = {}
        self._deprecated_modules: Set[str] = set()

        for since_vers, class_list in DEPRECATED_CLASSES.items():
            if since_vers <= sys.version_info:
                self._deprecated_classes.update(class_list)
        for since_vers, mod_list in DEPRECATED_MODULES.items():
            if since_vers <= sys.version_info:
                self._deprecated_modules.update(mod_list)

    def open(self) -> None:
        self._deprecated_modules.update(self.config.huawei_deprecated_modules)

    def deprecated_modules(self):
        """Callback returning the deprecated modules."""
        return self._deprecated_modules

    def deprecated_classes(self, module: str):
        return self._deprecated_classes.get(module, ())
        
    def check_deprecated_module(self, node, mod_path):
        """Checks if the module is deprecated."""
        for mod_name in self.deprecated_modules():
            if (mod_path == mod_name or mod_path.startswith(mod_name + ".")) and \
                not self.check_compatible_statement(node):
                self.add_message("huawei-deprecated-module", node=node, args=mod_path)
                
    def check_deprecated_class(self, node, mod_name, class_names):
        """Checks if the class is deprecated."""
        for class_name in class_names:
            if class_name in self.deprecated_classes(mod_name) and not self.check_compatible_statement(node):
                self.add_message(
                    "huawei-deprecated-class", node=node, args=(class_name, mod_name)
                )
                
    def check_compatible_statement(self, node):
        '''check deprecated module in try or exception nodes range'''
        if isinstance(node.parent, (nodes.TryExcept, nodes.ExceptHandler, nodes.If)):
            return True
        return False

    @check_messages(
        "huawei-deprecated-module",
        "huawei-deprecated-class",
    )
    def visit_import(self, node: nodes.Import) -> None:
        """Triggered when an import statement is seen."""
        for name in (name for name, _ in node.names):
            self.check_deprecated_module(node, name)
            if "." in name:
                # Checking deprecation for import module with class
                mod_name, class_name = name.split(".", 1)
                self.check_deprecated_class(node, mod_name, (class_name,))

    @check_messages(
        "huawei-deprecated-module",
        "huawei-deprecated-class",
    )
    def visit_importfrom(self, node: nodes.ImportFrom) -> None:
        """Triggered when a from statement is seen."""
        basename = node.modname
        basename = get_import_name(node, basename)
        self.check_deprecated_module(node, basename)
        class_names = (name for name, _ in node.names)
        self.check_deprecated_class(node, basename, class_names)

def register(linter):
    linter.register_checker(DeprecationChecker(linter))
