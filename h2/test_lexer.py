#!/usr/bin/python3.6
#
# test_lexer.py
#

import sys

from sly import Lexer

class TestLexer(Lexer):

    def __init__(self):
        self.lineno = 0

    # String containing ignored characters (between tokens)
    ignore = ' \t'

    # Other ignored patterns
    ignore_comment = r'\#.*'

    reserved_words = {'PRINT', 'BEGIN', 'END'}

    # Set of token names.   This is always required
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
        'COLON',
        'PERIOD',
    }

    # see https://stackoverflow.com/questions/2039795/regular-expression-for-a-string-literal-in-flex-lex

    # Regular expression rules for tokens
    ID      = r'[a-zA-Z_][a-zA-Z0-9_]*'
    STRING  = r'\"(\\.|[^"\\])*\"'
    PLUS    = r'\+'
    MINUS   = r'-'
    TIMES   = r'\*'
    DIVIDE  = r'/'
    LPAREN  = r'\('
    RPAREN  = r'\)'
    BOOL    = r'True|False'
    EQ      = r'=='       # MUST APPEAR FIRST! (LONGER)
    ASSIGN  = r'='
    GE      = r'>='
    LE      = r'<='
    GT      = r'>'
    LT      = r'<'
    LBRACKET= r'\['
    RBRACKET= r'\]'
    COMMA   = r','
    COLON   = r':'
    PERIOD  = r'\.'

    @_(r'\d+')
    def NUMBER(self, token):
        token.value = int(token.value)   # Convert to a numeric value
        return token

    def ID(self, token):
        if token.value in self.reserved_words:
            token.type = token.value.upper()
            #print("Keyword {} at line {} char {}".format(token.type, self.lineno + 1, self.find_column(token.value, token)))
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
    @_(r'\n+')
    def ignore_newline(self, token):
        self.lineno += token.value.count('\n')

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
                print('type=%r, value=%r' % (tok.type, tok.value))
    else:
        while True:
            try:
                text = input()
                for tok in lexer.tokenize(text):
                    print('type=%r, value=%r' % (tok.type, tok.value))
            except EOFError:
                break


if __name__ == '__main__':
    main()

