# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

import tokenize

from astroid import nodes
from eradicate import Eradicator

from pylint.checkers import BaseTokenChecker
from pylint.checkers.utils import check_messages
from pylint.interfaces import ITokenChecker, IRawChecker


class CommentOutChecker(BaseTokenChecker):
    __implements__ = (ITokenChecker, IRawChecker)
    name = 'comment-out'
    priority = -1
    
    msgs = {
        'H3115': (
            'Delete unnecessary code segments,do not comment them out.',
            'comment-out-code',
            'Delete unnecessary code segments.do not comment them out.'
        ),
    }
    
    DEFUALT_WHITE_LIST = [
        u'[\u4e00-\u9fa5]+'
    ]
    
    options = (
            (
                "default-comment-white-list",
                {
                    "default": "",
                    "type": "string"
                }
            ),
        )

    def __init__(self, linter=None):
        super().__init__(linter)
        self.module_path = None
        self._eradicator = Eradicator()
        
    def open(self):
        super().open()
        if self.config.default_comment_white_list.strip() != '':
            self.DEFUALT_WHITE_LIST.extend(self.config.default_comment_white_list.strip().split(','))
        self._eradicator.update_whitelist(self.DEFUALT_WHITE_LIST,extend_default=True)

    def process_tokens(self, tokens):
        comment_in_file = any(
            token.type == tokenize.COMMENT
            for token in tokens
        )
        if comment_in_file:
            self.check_comment_out_code()
            
    def check_comment_out_code(self):
        try:
            with open(self.module_path, encoding="utf-8") as reader:
                for line_index, line in enumerate(reader):
                    # aggressive is False indicates a Loose check, will decrease warn number
                    ret = self._eradicator.filter_commented_out_code(line, aggressive=False)
                    filtered_source = ''.join(ret)
                    if line == filtered_source:
                        continue
                    self.add_message(
                        "comment-out-code",
                        line=line_index+1,
                        col_offset=line.find('#')
                    )
        # ignore file open or read error
        except Exception as e:
            print(e)

    def process_module(self, module: nodes.Module) -> None:
        self.module_path = module.file

def register(linter):
    linter.register_checker(CommentOutChecker(linter))
