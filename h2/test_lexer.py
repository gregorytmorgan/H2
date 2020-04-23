#!/usr/bin/python3.6
#
# test_lexer.py
#

import sys
import ast

from sly import Lexer

Show_endlines = False
Show_comments = False

class TestLexer(Lexer):

    def __init__(self):
        self.lineno = 0

    # String containing ignored characters (between tokens)
    ignore = ' \t'

    # Other ignored patterns. See rule below
    #ignore_comment = r'\#.*'

    # token values that conflict with 'ID' token rule
    reserved_words = {'Print', 'Do', 'Done', 'Mission', 'True', 'False', 'Not'}

    # Set of token types.   This is always required
    tokens = {
        'ID',
        'NUMBER',
        'STRING',
        'PLUS',
        'MINUS',
        'TIMES',
        'DIVIDE',
        'ASSIGN',
        'LPAREN',
        'RPAREN',
        'BOOL',
        'EQ',
        'GE',
        'LE',
        'GT',
        'LT',
        'LBRACKET',
        'RBRACKET',
        'COMMA',
        'MISSION',
        'PRINT',
        'BLOCK_BEGIN',
        'BLOCK_END',
        'NOT',
        'COMMENT',
        'ENDLINE',
    }

    # see stackoverflow.com/questions/2039795/regular-expression-for-a-string-literal-in-flex-lex

    # Regular expression rules for tokens
    ID          = r'[a-zA-Z_][a-zA-Z0-9_]*'
    STRING      = r'\"(\\.|[^"\\])*\"'      # capture entire multi-line strings to simplify error handling
    BOOL        = r'True|False'             # see ID below
    PLUS        = r'\+'
    MINUS       = r'-'
    TIMES       = r'\*'
    DIVIDE      = r'/'
    EQ          = r'=='                     # MUST APPEAR BEFORE '=' (LONGER)
    ASSIGN      = r'='
    GE          = r'>='
    LE          = r'<='
    GT          = r'>'
    LT          = r'<'
    LPAREN      = r'\('
    RPAREN      = r'\)'
    LBRACKET    = r'\['
    RBRACKET    = r'\]'
    COMMA       = r','
    MISSION     = r'Mission'
    PRINT       = r'Print'
    NOT         = r'Not'
    BLOCK_BEGIN = r'Do'
    BLOCK_END   = r'Done'
    COMMENT     = r'\#.*'
    ENDLINE     = r'\n'

    @_(r'\d+')
    def NUMBER(self, token):
        token.value = int(token.value)   # Convert to a numeric value
        return token

    @_(r'\"(\\.|[^"\\])*\"')
    def STRING(self, token):
        try:
            token.value = ast.literal_eval(token.value) # Convert to an actual string vs string-in-a-string
        except Exception as e:
            print("{}: {} on line {}, char {}. Context: {}".format(e.__class__.__name__, e.msg, self.lineno, e.offset, e.text))

        return token

    def ID(self, token):
        if token.value in self.reserved_words:
            if token.value == 'True' or token.value == 'False':
                token.type = 'BOOL'
                token.value = ast.literal_eval(token.value)
            elif token.value == 'Do':
                token.type = 'BLOCK_BEGIN'
            elif token.value == 'Done':
                token.type = 'BLOCK_END'
            else:
                token.type = token.value.upper()
        return token

    # Compute column.
    #
    #     text is the input text string
    #     token is a token instance
    def find_column(self, text, token):
        last_cr = self.text.rfind('\n', 0, token.index)
        if last_cr < 0:
            last_cr = 0
        column = (token.index - last_cr)
        return column

    # Define a rule so we can track line numbers
    @_(r'\n')
    def ENDLINE(self, token):
        self.lineno += 1
        token.value = 'ENDLINE'
        return token

    def error(self, token):
        print("Line {}: Bad character '{}' at char {}".format(self.lineno, token.value[0], self.find_column(token.value[0], token)))
        self.index += 1

def main():
    import fileinput

    lexer = TestLexer()

    if len(sys.argv) > 1:
        lines = []
        with fileinput.input() as f:
            for line in f:
                lines.append(line)

            for tok in lexer.tokenize(''.join(lines)):
                if not Show_endlines and tok.type == 'ENDLINE':
                    continue

                if not Show_comments and tok.type == 'COMMENT':
                    continue

                print('type=%r, value=%r' % (tok.type, tok.value))
    else:
        while True:
            try:
                text = input()
                for tok in lexer.tokenize(text):
                    if not Show_endlines and tok.type == 'ENDLINE':
                        continue

                    if not Show_comments and tok.type == 'COMMENT':
                        continue

                    print('type=%r, value=%r' % (tok.type, tok.value))
            except EOFError:
                break


if __name__ == '__main__':
    main()

