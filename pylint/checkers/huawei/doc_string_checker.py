# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

import re

import astroid

from pylint.checkers import BaseChecker
from pylint.checkers.base.docstring_checker import _infer_dunder_doc_attribute
from pylint.checkers.huawei.utils.util import get_docstring_line
from pylint.checkers.utils import (
    check_messages,
    is_overload_stub,
    is_property_deleter,
    is_property_setter,
)
from pylint.interfaces import IAstroidChecker


class DocStringChecker(BaseChecker):
    __implements__ = IAstroidChecker
    name = 'doc-string-checker'
    priority = -1
    msgs = {
        "C0117": (
            "Docstrings for classes is indented back by four spaces.",
            "class-docstring-indents-four",
            'Document strings for classes and interfaces are written on the line next to the line where the class '
            'declaration (class ClassName:) is located and indented back by four spaces.',
        ),
        "C0118": (
            "Docstring for function is indented back by four spaces.",
            "function-docstring-indents-four",
            'The document string of the public function is written in the line next to the line where the function '
            'declaration (def FunctionName(self):) is located and four spaces are indented back.',
        ),
        "C0119": (
            "The module docstring indentation is not required.",
            "module-docstring-no-indents",
            'The module document string is written at the top of the file and before the import part. '
            'Indentation is not required.',
        ),
    }

    no_docstring_regex = re.compile("^_")

    def __init__(self, linter=None):
        super(DocStringChecker, self).__init__(linter)
        self.module_path = None

    @check_messages("module-docstring-no-indents",
                    "class-docstring-indents-four", "function-docstring-indents-four")
    def visit_module(self, node):
        self.module_path = node.file
        self._check_docstring("module", node)

    @check_messages("class-docstring-indents-four",
                    "function-docstring-indents-four", "module-docstring-no-indents")
    def visit_classdef(self, node):
        # skip private and magics, which all starts with an underscore.
        if self.no_docstring_regex.match(node.name):
            return
        self._check_docstring("class", node)

    @check_messages("function-docstring-indents-four",
                    "class-docstring-indents-four", "module-docstring-no-indents")
    def visit_functiondef(self, node):
        # skip private and magics, which all starts with an underscore.
        if self.no_docstring_regex.match(node.name):
            return
        ftype = "method" if node.is_method() else "function"
        if (
            is_property_setter(node) or
            is_property_deleter(node) or
            is_overload_stub(node)
        ):
            return

        if isinstance(node.parent.frame(), (astroid.ClassDef, astroid.Module)):
            self._check_docstring(ftype, node)
        else:
            return

    visit_asyncfunctiondef = visit_functiondef

    def _check_docstring(self, node_type, node):
        """check the node has a non empty docstring"""
        docstring = node.doc
        if docstring is None:
            docstring = _infer_dunder_doc_attribute(node)

        if docstring is not None and docstring.strip() is not None:
            self.docstring_format(node, docstring, node_type)

    def docstring_format(self, node, docstring, node_type):
        docs = docstring.split("\n")
        INDENT_OFFSET = 4
        if node_type == "class" and self.is_invalid_docstring_format(docs, node.col_offset + INDENT_OFFSET) and \
                self.is_invalid_file_docstring_format(node, node.col_offset + INDENT_OFFSET):
            self.add_message("class-docstring-indents-four", node=node)
        elif node_type == "module" and self.is_invalid_docstring_format(docs, 0) and \
                self.is_invalid_file_docstring_format(node, 0):
            # module node does not keep docstring's position information.
            # raw-parse source file to get the line number of docstring.
            self.add_message("module-docstring-no-indents",
                             line=get_docstring_line(node.file), node=node)
        elif (
            node_type in ["method", "function"] and
            self.is_invalid_docstring_format(
                docs, node.col_offset + INDENT_OFFSET) and 
            self.is_invalid_file_docstring_format(node, node.col_offset + INDENT_OFFSET)
        ):
            self.add_message("function-docstring-indents-four", node=node)

    @staticmethod
    def is_invalid_docstring_format(docs, indent):
        if len(docs) > 0:
            docs.pop(0)
        if len(docs) <= 0:
            return False
        end_doc = docs[-1]
        if end_doc != "" and not end_doc.isspace():
            return True
        if len(end_doc) != indent:
            return True
        for doc in docs:
            col_re = re.search(r'\S', doc, flags=0)
            if col_re:
                if col_re.span()[0] < indent:
                    return True
        return False
        
    def is_invalid_file_docstring_format(self, node, indent):
        docs = self.get_safe_doc_string(node)
        return self.is_invalid_docstring_format(docs, indent)
        
    def get_doc_string(self, node):
        '''
        Return docs of method, funtion, module or class.
        get docs from file, not from ast node

        :param node: Node considered
        :type node: astroid.Node
        :return: docs
        :rtype: list
        '''
        single_triple_quotation = "\'\'\'"
        double_triple_quotation = '\"\"\"'
        triple_quotation_length = len(double_triple_quotation)
        def line_endswith_triple_quotation(line):
            return line.endswith(single_triple_quotation) or line.endswith(double_triple_quotation)
        
        def line_startswith_triple_quotation(line):
            return line.startswith(single_triple_quotation) or line.startswith(double_triple_quotation)

        def get_doc_line(doc_str, is_doc_begin):
            doc_line = doc_str.strip('\r\n').strip('\n')
            if line_startswith_triple_quotation(doc_line.lstrip()) and is_doc_begin:
                doc_line = doc_line.lstrip().lstrip(single_triple_quotation).lstrip(double_triple_quotation)
            
            if line_endswith_triple_quotation(doc_line.rstrip()):
                doc_line = doc_line.rstrip().rstrip(single_triple_quotation).rstrip(double_triple_quotation)
            return doc_line        
        
        doc_start_line = node.lineno
        if node.body:
            doc_end_line = node.body[0].lineno
        else:
            # when node body is empty, end_lineno of node maybe None
            doc_end_line = node.end_lineno
        with open(self.module_path, encoding="utf-8") as reader:
            line_index  = 0
            doc_begin = False
            docs = []
            for line in reader:
                if (doc_start_line <= line_index) and (doc_end_line is None or line_index <= doc_end_line):
                    new_line = line.strip()
                    if line_startswith_triple_quotation(new_line) and not doc_begin:
                        doc_begin = True
                        if line_endswith_triple_quotation(new_line) and len(new_line) > triple_quotation_length:
                            docs.append(get_doc_line(line, doc_begin))
                            doc_begin = False
                            # oneline doc string is end
                            break
                    elif line_endswith_triple_quotation(new_line) and doc_begin:
                        doc_begin = False
                        docs.append(get_doc_line(line, doc_begin))
                        # multiline doc string is end
                        break
                    if doc_begin:
                        docs.append(get_doc_line(line, doc_begin))
                line_index += 1
            return docs
            
    def get_safe_doc_string(self, node):
        '''
            safe open module file
        '''
        try:
            return self.get_doc_string(node)
        except Exception as e:
            return []

def register(linter):
    linter.register_checker(DocStringChecker(linter))
