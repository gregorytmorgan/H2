#!/usr/bin/python3.6
#
# test_parser.py
#

import ast
import sys
from sly import Lexer
from sly import Parser
from simple_node import SimpleNode as node

class Lexer(Lexer):

    def __init__(self):
        self.lineno = 0

    # String containing ignored characters (between tokens)
    ignore = ' \t'

    # Other ignored patterns
    ignore_comment = r'\#.*'

    # token values that conflict with 'ID' token rule
    reserved_words = {
        'Do',
        'Done',
        'True',
        'False'
    }

    # Set of token types.   This is always required
    tokens = {
        'ID',
        'NUMBER',
        'STRING',
        'BOOL',
        'EQ',
        'PLUS',
        'MINUS',
        'TIMES',
        'DIVIDE',
        'ASSIGN',
        'LPAREN',
        'RPAREN',
        'BLOCK_BEGIN',
        'BLOCK_END',
        'COMMENT',
        'ENDLINE',
    }

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

    LPAREN      = r'\('
    RPAREN      = r'\)'

    BLOCK_BEGIN = r'Do'
    BLOCK_END   = r'Done'

    COMMENT     = r'\#.*'
    ENDLINE     = r'\n'


    @_(r'\d+')
    def NUMBER(self, token):
        token.value = ast.literal_eval(token.value)   # Convert to a numeric value
        return token

    @_(r'\"(\\.|[^"\\])*\"')
    def STRING(self, token):
        try:
            token.value = ast.literal_eval(token.value) # safely eval a string(vs string within a string)
        except Exception as e:
            print("{}: {} on line {}, char {}. Context: {}".format(e.__class__.__name__, e.msg, self.lineno, e.offset, e.text))

        return token

    def ID(self, token):
        if token.value in self.reserved_words:
            if token.value == 'True' or token.value == 'False':
                token.type = 'BOOL'
                token.value = ast.literal_eval(token.value) # safely eval literal string to type
            elif token.value == 'Do':
                token.type = 'BLOCK_BEGIN'
            elif token.value == 'Done':
                token.type = 'BLOCK_END'
            else:
                token.type = token.value.upper()
        return token

    # Define a rule so we can track line numbers
    @_(r'\n')
    def ENDLINE(self, token):
        self.lineno += 1
        token.value = 'ENDLINE'
        return token

    def error(self, token):
        print("Line {}: Bad character '{}' at char {}".format(self.lineno, token.value[0], self.find_column(token.value[0], token)))
        self.index += 1

class Parser(Parser):
    debugfile = 'parser.out'

    tokens = Lexer.tokens

    precedence = (
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIVIDE'),
        ('right', 'UMINUS'),            # Unary minus operator
    )

    def __init__(self):
        self.names = { }
        self.line_start = 0
        self.char_adj = 0

    def error(self, p):
        if p:
            # the error char(p.index) will not likely be accurate here so just provide line number
            print("Syntax error at line {}. Token {}({})".format(p.lineno, p.type, p.value))
            #self.errok()
        else:
            print("Syntax error at EOF")

    # code
    @_('statements')
    def code(self, p):
        if p.statements is None:
            pass
        else:
            return node('code', [p.statements])

    # code
#    @_('BLOCK_BEGIN statements BLOCK_END')
#    def code(self, p):
#
#        if p.statements is None:
#            pass
#        else:
#            return node('code', [p.statements])

#    # statements
#    @_('statements statement')
#    def statements(self, p):
#
#        #print("statements: {}".format(p.statements))
#        #print("statement: {}".format(p.statement))
#
#        if p.statements is None and p.statement is None:
#            return None
#        elif p.statement is None:
#            return node('statements', [p.statements])
#        elif p.statements is None:
#            return node('statements', [node('statement', [p.statement])])
#        else:
#            return node('statements', [p.statements, node('statement', [p.statement])])

    # statements
    @_('statement')
    def statements(self, p):
        if p.statement is None:
            node('code')
        else:
            return node('code', [p.statement])

    # statements
    @_('statements statement')
    def statements(self, p):
        if p.statements is None and p.statement is None:
            return None
        elif p.statement is None:
            return node('statements', [p.statements])
        elif p.statements is None:
            return node('statements', [node('statement', [p.statement])])
        else:
            return node('statements', [p.statements, node('statement', [p.statement])])

#    @_('statement',
#       'error')
#    def statements(self, p):
#        #return node('statement', [p.statement])
#        if hasattr(p, 'statement'):
#            #print("{}".format(p.statement.lineno))
#            print("{}".format(p.statement))
#            #self.line_start = p.statement.index
#
#            if p.statement is None:
#                return None
#            else:
#                return node('statement', [p.statement])
#        else:
#            self.line_start = p.error.index
#            return node(('error', "There was statement error at line {}, char {}. Token {}({})".format(p.error.lineno, p.error.index - self.line_start, p.error.type, p.error.value)))

    # statement
    @_('ID ASSIGN expr',
       'ID ASSIGN error')
    def statement(self, p):
        self.line_start = p.index
        if hasattr(p, 'expr'):
            return node(('assign', p.ID), [p[2]])
        elif hasattr(p, 'bexpr'):
            return node(('assign', p.ID), [p[2]])
        else:
            return node(('error', "There was an assignment error at line {}, char {}. Token {}({})".format(p.error.lineno, p.error.index - self.line_start, p.error.type, p.error.value)))

    # codeblock
    @_('BLOCK_BEGIN statements BLOCK_END')
    def codeblock(self, p):
        return node('codeblock', [p.statements])

    @_('MINUS expr %prec UMINUS')
    def expr(self, p):
        return node('uminus', [p.expr])

    # expr
    @_('NUMBER')
    def expr(self, p):
        return node(('number', p.NUMBER))

    @_('BOOL')
    def expr(self, p):
        return node(('bool', p.BOOL))

    @_('ID')
    def expr(self, p):
        return node(('id', p.ID))

    @_('STRING')
    def expr(self, p):
        return node(('string', p.STRING))

    @_('expr PLUS expr',
       'expr MINUS expr',
       'expr TIMES expr',
       'expr DIVIDE expr')  # 'expr error expr' cause 5 s/r conflicts
    def expr(self, p):
        return node(p[1], [p.expr0, p.expr1])

    @_('ENDLINE')
    def statement(self, p):
        self.char_adj += 1
        return None

def main():
    import fileinput

    parser = Parser()

    lexer = Lexer()

    if len(sys.argv) > 1:
        with fileinput.input() as f:
            lines = []
            for line in f:
                lines.append(line)

            result = parser.parse(lexer.tokenize(''.join(lines)))
            print("{}".format(result))
    else:
        while True:
            try:
                text = input()
                result = parser.parse(lexer.tokenize(text))
                print("{}".format(result))
            except EOFError:
                break

if __name__ == '__main__':
    main()
