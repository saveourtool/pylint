# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

import tokenize
from typing import List
import itertools

import astroid

from pylint.checkers import BaseTokenChecker
from pylint.checkers.utils import check_messages
from pylint.interfaces import IAstroidChecker, ITokenChecker


class MultilineComprehensionChecker(BaseTokenChecker):
    __implements__ = (ITokenChecker, IAstroidChecker)
    name = 'multiline-comprehension'
    priority = -1
    
    msgs = {
        'H2309': (
            '%s',
            'multiline-comprehension',
            'it is recommended that the left parentheses and the right parentheses be placed on the same line,'
            'or that the left parentheses be placed on a separate line for the first time.'
        ),
    }

    def __init__(self, linter=None):
        super().__init__(linter)
        self.tokens = []
        
    @staticmethod 
    def get_first_elt_or_item_token(tokens):
        '''
        get first elem or item of sequence expression
        such as list,set,tuple and dict
           
        :param tokens: token list with surrounding node
        :type tokens: list
        :return: first elem or item 
        :rtype: tokenize.TokenInfo
        '''
        for token in tokens[1:]:
            if token.type == tokenize.NL:
                continue
            return token
            
    @staticmethod 
    def get_last_elt_or_item_token(tokens):
        '''
        get last elem or item of sequence expression
        such as list,set,tuple and dict
        
        :param tokens: token list with surrounding node
        :type tokens: list
        :return: first elem or item 
        :rtype: tokenize.TokenInfo
        '''
        for token in tokens[::-1][1:]:
            if token.type == tokenize.NL:
                continue
            return token

    @staticmethod    
    def is_matched_tokens(tokens):
        '''
        Check whether the first and last tokens in the token list match.
        
        :param tokens: token list with surrounding node
        :type tokens: list
        :return: the first and last tokens in the token list matched or not
        :rtype: bool
        '''
        if not tokens:
            return False
        if (
            tokens[0].type == tokenize.OP and tokens[0].string in ['(' , '[', '{']
        ) and (
            tokens[-1].type == tokenize.OP and tokens[-1].string in [')' , ']', '}']
        ):
            return True
        return False

    @check_messages("multiline-comprehension")
    def visit_assign(self, node) -> None:
        self.check_assign(node)
        
    visit_annassign = visit_assign

    def check_assign(self, node):
        def check_parentheses_lineno(tokens):
            '''
               Check whether the left and right parentheses line numbers are the same. 
            '''
            left_token_lineno, _ = tokens[0].start
            right_token_lineno, _ = tokens[-1].start
            if left_token_lineno == right_token_lineno:
                return True
            return False

        if isinstance(node.value, (astroid.Tuple, astroid.List, astroid.Set, astroid.Dict)):
            tokens = self._get_tokens_with_surrounding(node.value)
            if not self.is_matched_tokens(tokens):
                return
            if check_parentheses_lineno(tokens):
                return
            self.check_left_parentheses(tokens, node.value)
            self.check_right_parentheses(tokens, node)

        elif isinstance(node.value, (astroid.DictComp, astroid.ListComp, astroid.SetComp, astroid.GeneratorExp)):
            self.check_multiline_comprehension_generators(node.value)
            self.check_multiline_comprehension_segments(node.value)
            
    def check_left_parentheses(self, tokens, node):
        '''
            Either the left parenthesis is on the same line as the right parenthesis, 
            or the first line breaks after the left parenthesis, 
        '''
        src_msg = "Newline should take place right after starting bracket '%s' in a multiline %s expression"
        left_token_lineno, left_token_col_offset = tokens[0].start
        first_el_token_lineno, _ = self.get_first_elt_or_item_token(tokens).start
        if first_el_token_lineno == left_token_lineno:
            self.add_message(
                'multiline-comprehension',
                line=left_token_lineno,
                col_offset=left_token_col_offset,
                args=src_msg % (tokens[0].string, node.name)
            )

    def check_right_parentheses(self, tokens, node):
        '''
            the right parenthesis on a separate line and must align left with node col_offset
        '''
        src_msg = "Closing bracket '%s' should take up a whole line and left-align with the statement"
        last_el_token_lineno, _ = self.get_last_elt_or_item_token(tokens).start
        right_token_lineno, right_token_col_offset = tokens[-1].start
        if last_el_token_lineno == right_token_lineno or (
            node.col_offset != right_token_col_offset
        ):
            self.add_message(
                'multiline-comprehension',
                line=right_token_lineno,
                col_offset=right_token_col_offset,
                args=src_msg % (tokens[-1].string)
            )

    def process_tokens(self, tokens):
        self.tokens = tokens
        
    def leave_module(self, node):
        self.tokens = []
        
    def _get_tokens_with_surrounding(self, node) -> List[tokenize.TokenInfo]:
        '''
        get token list with surrounding node,such as tuple,list,set and dict expression
        
        :param node: Node considered
        :type node: astroid.Node
        :return: token list 
        :rtype: list(tokenize.TokenInfo)
        '''
        start_index, end_index = None, None
        lineno = node.lineno
        for i, token in enumerate(self.tokens):
            if (
                node.lineno, node.col_offset
            ) <= token.start <= (
                node.end_lineno, node.end_col_offset
            ):
                if start_index is None:
                    start_index = i
            else:
                if end_index is None and start_index is not None:
                    end_index = i
                    break
        return self.tokens[start_index:end_index-1]
        
    def check_multiline_comprehension_generators(self, node):
        """
        A comprehension expression should place each of its generators on a separate line.
        """
        for generator1, generator2 in itertools.combinations(node.generators, 2):
            # continuous comparison syntax sugar
            if (
                generator1.target.lineno <= generator2.target.lineno <= generator1.iter.end_lineno
            ) or (
                generator2.target.lineno <= generator1.target.lineno <= generator2.iter.end_lineno
            ):
                self.pop_comprehension_error(node.lineno, node.col_offset)
                break

    def pop_comprehension_error(self, line, col):
        msg = 'Different segments of a comprehension expression should be in different lines, or in a single line'
        self.add_message(
            'multiline-comprehension',
            line=line,
            col_offset=col,
            args=msg
        )

    def check_multiline_comprehension_segments(self, node):
        """
        A multiline comprehension expression should place each of its segments (map, generator, filter) on a separate line.
        """

        if node.lineno == node.end_lineno:
            return # single line comprehension

        seen_line_nos = set()

        for generator in node.generators:
            if generator.target.lineno in seen_line_nos:
                self.pop_comprehension_error(generator.target.lineno, generator.target.col_offset)
            seen_line_nos.add(generator.target.lineno)

            for if_clause in generator.ifs:
                if if_clause.lineno in seen_line_nos:
                    self.pop_comprehension_error(if_clause.lineno, if_clause.col_offset)
                seen_line_nos.add(if_clause.lineno)

        if isinstance(node, astroid.DictComp):
            if node.value.lineno in seen_line_nos:
                self.pop_comprehension_error(node.key.lineno, node.key.col_offset)
            seen_line_nos.add(node.value.lineno)
        else:
            if node.elt.lineno in seen_line_nos:
                self.pop_comprehension_error(node.elt.lineno, node.elt.col_offset)
            seen_line_nos.add(node.elt.lineno)
            
def register(linter) -> None:
    linter.register_checker(MultilineComprehensionChecker(linter))
