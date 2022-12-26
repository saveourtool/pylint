# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

import re
from typing import Dict, Optional, Pattern, Tuple

import astroid

import pylint.checkers.huawei.utils.util as huawei_util
from pylint import constants, interfaces
from pylint.checkers import BaseChecker, utils
from pylint.checkers.base.name_checker.checker import (
    BUILTIN_PROPERTY,
    DEFAULT_PATTERNS,
    _is_multi_naming_match,
    _redefines_import,
    TYPING_TYPE_VAR_QNAME,
)
from pylint.checkers.base.name_checker.naming_style import (
    DEFAULT_NAMING_STYLES,
    KNOWN_NAME_TYPES,
    KNOWN_NAME_TYPES_WITH_STYLE,
    AnyStyle,
    CamelCaseStyle,
    NamingStyle,
    PascalCaseStyle,
    UpperCaseStyle,
)
from pylint.checkers.utils import (
    check_messages,
    is_property_deleter,
    is_property_setter,
)
from pylint.interfaces import IAstroidChecker


class SnakeCaseStyle(NamingStyle):
    """Regex rules for snake_case naming style."""

    CLASS_NAME_RGX = re.compile(r"[^\W\dA-Z][^\WA-Z]+$")
    MOD_NAME_RGX = re.compile(r"[^\W\dA-Z][^\WA-Z]*$")
    CONST_NAME_RGX = re.compile(r"([^\W\dA-Z][^\WA-Z]*|__.*__)$")
    COMP_VAR_RGX = re.compile(r"[^\W\dA-Z][^\WA-Z]*$")
    DEFAULT_NAME_RGX = re.compile(
        r"([^\W\dA-Z][^\WA-Z]*|_[^\WA-Z]*|__[^\WA-Z\d_][^\WA-Z]+__)$"
    )
    CLASS_ATTRIBUTE_RGX = re.compile(r"([^\W\dA-Z][^\WA-Z]*|__.*__)$")

NAMING_STYLES = {
    "snake_case": SnakeCaseStyle,
    "camelCase": CamelCaseStyle,
    "PascalCase": PascalCaseStyle,
    "UPPER_CASE": UpperCaseStyle,
    "any": AnyStyle,
}

def _create_naming_options():
    name_options = []
    for name_type in sorted(KNOWN_NAME_TYPES):
        human_readable_name = constants.HUMAN_READABLE_TYPES[name_type]
        name_type_hyphened = name_type.replace("_", "-")

        help_msg = f"Regular expression matching correct {human_readable_name} names. "
        if name_type in KNOWN_NAME_TYPES_WITH_STYLE:
            help_msg += f"Overrides {name_type_hyphened}-naming-style. "
        help_msg += f"If left empty, {human_readable_name} names will be checked with the set naming style."

        # Add style option for names that support it
        if name_type in KNOWN_NAME_TYPES_WITH_STYLE:
            default_style = DEFAULT_NAMING_STYLES[name_type]
            name_options.append(
                (
                    f"huawei-{name_type_hyphened}-naming-style",
                    {
                        "default": default_style,
                        "type": "choice",
                        "choices": list(NAMING_STYLES.keys()),
                        "metavar": "<style>",
                        "help": f"Naming style matching correct {human_readable_name} names.",
                    },
                )
            )

        name_options.append(
            (
                f"huawei-{name_type_hyphened}-rgx",
                {
                    "default": None,
                    "type": "regexp",
                    "metavar": "<regexp>",
                    "help": help_msg,
                },
            )
        )
    return tuple(name_options)


def _get_properties(config):
    """Returns a tuple of property classes and names.

    Property classes are fully qualified, such as 'abc.abstractproperty' and
    property names are the actual names, such as 'abstract_property'.
    """
    property_classes = {BUILTIN_PROPERTY}
    property_names = set()  # Not returning 'property', it has its own check.
    if config is not None:
        property_classes.update(config.huawei_property_classes)
        property_names.update(
            prop.rsplit(".", 1)[-1] for prop in config.huawei_property_classes
        )
    return property_classes, property_names


def _determine_function_name_type(node: astroid.FunctionDef, config=None):
    """Determine the name type whose regex the function's name should match.

    :param node: A function node.
    :param config: Configuration from which to pull additional property classes.
    :type config: :class:`optparse.Values`

    :returns: One of ('function', 'method', 'attr')
    :rtype: str
    """
    property_classes, property_names = _get_properties(config)
    if not node.is_method():
        return "function"

    if is_property_setter(node) or is_property_deleter(node):
        # If the function is decorated using the prop_method.{setter,getter}
        # form, treat it like an attribute as well.
        return "attr"

    decorators = node.decorators.nodes if node.decorators else []
    for decorator in decorators:
        # If the function is a property (decorated with @property
        # or @abc.abstractproperty), the name type is 'attr'.
        if isinstance(decorator, astroid.Name) or (
            isinstance(decorator, astroid.Attribute)
            and decorator.attrname in property_names
        ):
            inferred = utils.safe_infer(decorator)
            if (
                inferred
                and hasattr(inferred, "qname")
                and inferred.qname() in property_classes
            ):
                return "attr"
    return "method"


class InvalidNameChecker(BaseChecker):
    __implements__ = IAstroidChecker
    name = 'huawei-invalid-name'
    priority = -1

    msgs = {
        'H2101': (
            '%s name "%s" doesn\'t conform to %s',
            'huawei-invalid-name',
            "Used when the name doesn't conform to naming rules "
            "associated to its type (constant, variable, class...).",
        ),
    }

    options = (
        (
            "huawei-invalid-name-check-members",
            {
                "default": ("module", "const", "class", "function", "method", "attr", "argument",
                            "variable", "class_attribute", "inlinevar"),
                "type": "csv",
                "metavar": "",
                "help": "",
            },
        ),
        (
            "huawei-good-names",
            {
                "default": ("i", "j", "k", "ex", "Run", "_"),
                "type": "csv",
                "metavar": "<names>",
                "help": "Good variable names which should always be accepted,"
                " separated by a comma.",
            },
        ),
        (
            "huawei-good-names-rgxs",
            {
                "default": "",
                "type": "regexp_csv",
                "metavar": "<names>",
                "help": "Good variable names regexes, separated by a comma. If names match any regex,"
                " they will always be accepted",
            },
        ),
        (
            "huawei-include-naming-hint",
            {
                "default": False,
                "type": "yn",
                "metavar": "<y_or_n>",
                "help": "Include a hint for the correct naming format with invalid-name.",
            },
        ),
        (
            "huawei-property-classes",
            {
                "default": ("abc.abstractproperty",),
                "type": "csv",
                "metavar": "<decorator names>",
                "help": "List of decorators that produce properties, such as "
                "abc.abstractproperty. Add to this list to register "
                "other decorators that produce valid properties. "
                "These decorators are taken in consideration only for invalid-name.",
            },
        ),
    ) + _create_naming_options()

    def __init__(self, linter=None):
        super(InvalidNameChecker, self).__init__(linter)
        
    @staticmethod
    def check_is_global(node, name):
        globs = node.root().globals
        if name in globs and len(globs[name]) > 1:
            return True
        return False

    def open(self):
        regexps, hints = self._create_naming_rules()
        self._name_regexps = regexps
        self._name_hints = hints
        self._good_names_rgxs_compiled = [
            re.compile(rgxp) for rgxp in self.config.huawei_good_names_rgxs
        ]

    def _create_naming_rules(self) -> Tuple[Dict[str, Pattern[str]], Dict[str, str]]:
        regexps: Dict[str, Pattern[str]] = {}
        hints: Dict[str, str] = {}

        for name_type in KNOWN_NAME_TYPES:
            if name_type in KNOWN_NAME_TYPES_WITH_STYLE:
                naming_style_name = getattr(
                    self.config, f"huawei_{name_type}_naming_style")
                regexps[name_type] = NAMING_STYLES[naming_style_name].get_regex(
                    name_type
                )
            else:
                naming_style_name = "predefined"
                regexps[name_type] = DEFAULT_PATTERNS[name_type]

            custom_regex_setting_name = f"huawei_{name_type}_rgx"
            custom_regex = getattr(self.config, custom_regex_setting_name, None)
            if custom_regex is not None:
                regexps[name_type] = custom_regex

            if custom_regex is not None:
                hints[name_type] = f"{custom_regex.pattern!r} pattern"
            else:
                hints[name_type] = f"{naming_style_name} naming style"

        return regexps, hints

    @check_messages("huawei-invalid-name")
    def visit_module(self, node):
        self._check_name("module", node.name.split(".")[-1], node)
        self.if_main = None

    @check_messages("huawei-invalid-name")
    def visit_if(self, node):
        if self.if_main or \
                not node.parent or \
                not isinstance(node.parent, astroid.Module):
            return
        if huawei_util.check_if_main(node):
            self.if_main = node

    @check_messages("huawei-invalid-name")
    def leave_if(self, node):
        if node is self.if_main:
            self.if_main = None

    @check_messages("huawei-invalid-name")
    def visit_classdef(self, node):
        self._check_name("class", node.name, node)
        for attr, anodes in node.instance_attrs.items():
            if not any(node.instance_attr_ancestors(attr)):
                self._check_name("attr", attr, anodes[0])

    @check_messages("huawei-invalid-name")
    def visit_functiondef(self, node):
        # Do not emit any warnings if the method is just an implementation
        # of a base class method.
        confidence = interfaces.HIGH
        if node.is_method():
            if utils.overrides_a_method(node.parent.frame(), node.name):
                return
            confidence = (
                interfaces.INFERENCE
                if utils.has_known_bases(node.parent.frame())
                else interfaces.INFERENCE_FAILURE
            )

        self._check_name(
            _determine_function_name_type(node, config=self.config),
            node.name,
            node,
            confidence,
        )
        # Check argument names
        args = node.args.args
        if args is not None:
            self._recursive_check_names(args, node)

    visit_asyncfunctiondef = visit_functiondef

    @check_messages("huawei-invalid-name")
    def visit_assignname(self, node: astroid.AssignName) -> None:
        """Check module level assigned names."""
        frame = node.frame(future=True)
        assign_type = node.assign_type()

        # Check names defined in comprehensions
        if isinstance(assign_type, astroid.Comprehension):
            self._check_name("inlinevar", node.name, node)

        # Check names defined in module scope
        elif isinstance(frame, astroid.Module):
            # Check names defined in Assign nodes
            if isinstance(assign_type, astroid.Assign):
                inferred_assign_type = utils.safe_infer(assign_type.value)

                # Check TypeVar's assigned alone or in tuple assignment
                if isinstance(node.parent, astroid.Assign) and self._assigns_typevar(
                    assign_type.value
                ):
                    self._check_name("typevar", assign_type.targets[0].name, node)
                elif (
                    isinstance(node.parent, astroid.Tuple)
                    and isinstance(assign_type.value, astroid.Tuple)
                    # protect against unbalanced tuple unpacking
                    and node.parent.elts.index(node) < len(assign_type.value.elts)
                    and self._assigns_typevar(
                        assign_type.value.elts[node.parent.elts.index(node)]
                    )
                ):
                    self._check_name(
                        "typevar",
                        assign_type.targets[0].elts[node.parent.elts.index(node)].name,
                        node,
                    )

                # Check classes (TypeVar's are classes so they need to be excluded first)
                elif isinstance(inferred_assign_type, astroid.ClassDef):
                    self._check_name("class", node.name, node)

                # Don't emit if the name redefines an import in an ImportError except handler.
                # huawei in-place change to pylint.
                # skip constants wrapped in (if __name__ == '__main__':) block.
                elif not _redefines_import(node) and isinstance(
                    inferred_assign_type, astroid.Const
                )and self.if_main == None and not self.check_is_global(node, node.name): 
                    self._check_name("const", node.name, node)
            # Check names defined in AnnAssign nodes
            elif isinstance(
                assign_type, astroid.AnnAssign
            ) and utils.is_assign_name_annotated_with(node, "Final"):
                self._check_name("const", node.name, node)

        # Check names defined in function scopes
        elif isinstance(frame, astroid.FunctionDef):
            # global introduced variable aren't in the function locals
            if node.name in frame and node.name not in frame.argnames():
                if not _redefines_import(node):
                    self._check_name("variable", node.name, node)

        # Check names defined in class scopes
        elif isinstance(frame, astroid.ClassDef):
            if not list(frame.local_attr_ancestors(node.name)):
                for ancestor in frame.ancestors():
                    if (
                        ancestor.name == "Enum"
                        and ancestor.root().name == "enum"
                        or utils.is_assign_name_annotated_with(node, "Final")
                    ):
                        self._check_name("class_const", node.name, node)
                        break
                else:
                    self._check_name("class_attribute", node.name, node)

    def _recursive_check_names(self, args, node):
        """check names in a possibly recursive list <arg>"""
        for arg in args:
            if isinstance(arg, astroid.AssignName):
                self._check_name("argument", arg.name, node)
            else:
                self._recursive_check_names(arg.elts, node)

    def _find_name_group(self, node_type):
        return self._name_group.get(node_type, node_type)

    def _raise_name_warning(
        self,
        prevalent_group: Optional[str],
        node: astroid.NodeNG,
        node_type: str,
        name: str,
        confidence,
        warning: str = "huawei-invalid-name",
    ) -> None:
        type_label = constants.HUMAN_READABLE_TYPES[node_type]
        hint = self._name_hints[node_type]
        if prevalent_group:
            # This happens in the multi naming match case. The expected
            # prevalent group needs to be spelled out to make the message
            # correct.
            hint = f"the `{prevalent_group}` group in the {hint}"
        if self.config.huawei_include_naming_hint:
            hint += f" ({self._name_regexps[node_type].pattern!r} pattern)"
        args = (
            (type_label.capitalize(), name, hint)
            if warning == "huawei-invalid-name"
            else (type_label.capitalize(), name)
        )

        self.add_message(warning, node=node, args=args, confidence=confidence)
        self.linter.stats.increase_bad_name(node_type, 1)

    def _name_allowed_by_regex(self, name: str) -> bool:
        return name in self.config.huawei_good_names or any(
            pattern.match(name) for pattern in self._good_names_rgxs_compiled
        )

    def _check_name(self, node_type, name, node, confidence=interfaces.HIGH):
        """check for a name using the type's regexp"""

        def _should_exempt_from_invalid_name(node):
            if node_type == "variable":
                inferred = utils.safe_infer(node)
                if isinstance(inferred, astroid.ClassDef):
                    return True
            return False
        # filter unrelated node types
        check_members = getattr(
            self.config, 'huawei_invalid_name_check_members')
        if node_type not in check_members:
            return
        
        if self._name_allowed_by_regex(name=name):
            return
        regexp = self._name_regexps[node_type]
        match = regexp.match(name)

        if _is_multi_naming_match(match, node_type, confidence):
            name_group = self._find_name_group(node_type)
            bad_name_group = self._bad_names.setdefault(name_group, {})
            warnings = bad_name_group.setdefault(match.lastgroup, [])
            warnings.append((node, node_type, name, confidence))

        if match is None and not _should_exempt_from_invalid_name(node):
            self._raise_name_warning(None, node, node_type, name, confidence)
        
        # Check TypeVar names for variance suffixes
        if node_type == "typevar":
            self._check_typevar_variance(name, node)

    @staticmethod
    def _assigns_typevar(node: Optional[astroid.NodeNG]) -> bool:
        """Check if a node is assigning a TypeVar."""
        if isinstance(node, astroid.Call):
            inferred = utils.safe_infer(node.func)
            if (
                isinstance(inferred, astroid.ClassDef)
                and inferred.qname() == TYPING_TYPE_VAR_QNAME
            ):
                return True
        return False


def register(linter):
    linter.register_checker(InvalidNameChecker(linter))
