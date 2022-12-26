# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

import tokenize

from pylint.checkers import BaseChecker
from pylint.checkers.huawei.utils.util import get_docstring_line
from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker, ITokenChecker


class HeaderCopyrightChecker(BaseChecker):
    __implements__ = IAstroidChecker, ITokenChecker
    name = 'header-copyright'
    priority = -1

    msgs = {
        'H2206': (
            '%s',
            'header-copyright',
            'File header comments should be placed before the module '
            'docstring, after the shebang and file encoding declaration.'
        ),
    }

    options = (
        (
            "copyright-pattern",
            {
                "default": '#\s*(版权所有|Copyright)',
                "type": "regexp",
            },
        ),
        (
            "shebang-pattern",
            {
                "default": '#!/usr/bin/env\s*python|#!/usr/bin/python',
                "type": "regexp",
            }
        ),
        (
            "encoding-pattern",
            {
                "default": '#\s*-\*-\s*coding:\s*utf-8\s*-\*-|#\s*coding\s*=\s*utf-8|#\s*coding:\s*utf-8',
                "type": "regexp",
            }
        ),
    )

    def __init__(self, linter=None):
        super(HeaderCopyrightChecker, self).__init__(linter)
        self.copyrights = []
        self.encoding_pos = 0
        self.shebang_pos = 0
        self.copyright_pattern = None
        self.pattern_shebang = None
        self.pattern_coding = None

    def open(self):
        super().open()
        if not self.copyright_pattern:
            self.copyright_pattern = self.config.copyright_pattern
        if not self.pattern_shebang:
            self.pattern_shebang = self.config.shebang_pattern
        if not self.pattern_coding:
            self.pattern_coding = self.config.encoding_pattern

    @check_messages("header-copyright")
    def visit_module(self, node):
        if len(self.copyrights) == 0:
            self.add_message('header-copyright', line=1,
                             args='Missing file header comments')
            return
        if node.body:
            module_begin = node.body[0].lineno
            docstring_line = get_docstring_line(node.file)
            if docstring_line:
                module_begin = min(module_begin, docstring_line)
            self.check_after_module(module_begin)

        max_pos = max(self.encoding_pos, self.shebang_pos)
        if max_pos != 0:
            self.check_before_shebang_or_encoding(max_pos)

    @check_messages("header-copyright")
    def leave_module(self, node):
        self.copyrights = []
        self.encoding_pos = 0
        self.shebang_pos = 0

    def check_after_module(self, module_begin):
        buggy_lines = []
        for copyright_pos in self.copyrights:
            if copyright_pos > module_begin:
                buggy_lines.append(copyright_pos)
        if buggy_lines:
            warn_msg = f'File header comments(line {buggy_lines}) should be placed '\
                       f'before module docstring and other statements(line {module_begin}).'
            self.add_message('header-copyright',
                             line=buggy_lines[0],
                             args=warn_msg)

    def check_before_shebang_or_encoding(self, max_pos):
        buggy_lines = []
        for copyright_pos in self.copyrights:
            if copyright_pos < max_pos:
                buggy_lines.append(copyright_pos)
        if buggy_lines:
            warn_msg = f'File header comments(line {buggy_lines}) should be placed '\
                       f'after shebang and file encoding declaration(line {max_pos}).'
            self.add_message('header-copyright',
                             line=buggy_lines[0],
                             args=warn_msg)

    @check_messages("header-copyright")
    def process_tokens(self, tokens):
        for token in tokens:
            if token.type == tokenize.COMMENT:
                matched = self.copyright_pattern.match(token.string)
                if matched:
                    self.copyrights.append(token.start[0])
                shebang = self.pattern_shebang.match(token.string)
                coding = self.pattern_coding.match(token.string)
                if shebang:
                    self.shebang_pos = token.start[0]
                if coding:
                    self.encoding_pos = token.start[0]


def register(linter):
    linter.register_checker(HeaderCopyrightChecker(linter))
