#!/usr/bin/python3.6
#
# test_parser.py
#

import sys

from sly import Parser
from test_lexer import TestLexer
from simple_node import SimpleNode as node

#class node(object):
#    def __init__(self, value, children = []):
#        self.value = value
#        self.children = children
#
#    def __str__(self, level=0):
#        ret = "\t" * level + repr(self.value) + "\n"
#        for child in self.children:
#            ret += child.__str__(level + 1)
#        return ret
#
#    def __repr__(self):
#        return '<tree node representation>'

class TestParser(Parser):
    debugfile = 'parser.out'

    tokens = TestLexer.tokens

    precedence = (
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIVIDE'),
        ('right', 'UMINUS'),            # Unary minus operator
        ('right', 'NOT'),
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
       'ID ASSIGN error',
       'ID ASSIGN bexpr')
    def statement(self, p):
        self.line_start = p.index
        #return node(('assign', p.ID), [p[2]])
        if hasattr(p, 'expr'):
            return node(('assign', p.ID), [p[2]])
        elif hasattr(p, 'bexpr'):
            return node(('assign', p.ID), [p[2]])
        else:
            return node(('error', "There was an assignment error at line {}, char {}. Token {}({})".format(p.error.lineno, p.error.index - self.line_start, p.error.type, p.error.value)))

    @_('PRINT LPAREN expr RPAREN',
       'PRINT LPAREN error RPAREN',
       'PRINT LPAREN bexpr RPAREN')
    def statement(self, p):
        self.line_start = p.index
        #return node('print', [p[2]])
        if hasattr(p, 'expr'):
            return node(('print'), [p[2]])
        elif hasattr(p, 'bexpr'):
            return node(('print'), [p[2]])
        else:
            return node(('error', "There was a print error at line {}, char {}. Token {}({})".format(p.error.lineno, p.error.index - self.line_start, p.error.type, p.error.value)))

    @_('COMMENT')
    def statement(self, p):
        self.char_adj = len(p.COMMENT)
        self.line_start = p.index
        return None

    @_('MISSION LPAREN STRING RPAREN codeblock')
    def statement(self, p):
        self.line_start = p.index
        return node(('mission', p.STRING), [p.codeblock])

    # codeblock
    @_('BLOCK_BEGIN statements BLOCK_END')
    def codeblock(self, p):
        return node('codeblock', [p.statements])

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
#        if hasattr(p, 'expr'):
#            return node(p[1], [p.expr0, p.expr1])
#        else:
#            print("{}".format(list(self.tokens)[0:4]))
#            return node(('error', "There was an operator error at line {}, char {}. Token {}({})".format(p.error.lineno, p.error.index - self.line_start, p.error.type, p.error.value)))

    @_('LPAREN expr RPAREN',
       'LPAREN error RPAREN') # 'LPAREN error RPAREN'
    def expr(self, p):
        #return p[1]
        if hasattr(p, 'expr'):
            return p[1]
        else:
            return node(('error', "There was an operator error at line {}, char {}. Token {}({})".format(p.error.lineno, p.error.index - self.line_start - self.char_adj, p.error.type, p.error.value)))


    @_('MINUS expr %prec UMINUS')
    def expr(self, p):
        return node('uminus', [p.expr])

    # bexpr
    @_('expr EQ expr',
       'expr GT expr',
       'expr LT expr',
       'expr GE expr',
       'expr LE expr')
    def bexpr(self, p):
        return node(p[1], [p.expr0, p.expr1])

    @_('LPAREN bexpr RPAREN')
    def bexpr(self, p):
        return p[1]

    @_('ENDLINE')
    def statement(self, p):
        self.char_adj += 1
        return None

def main():
    import fileinput

    parser = TestParser()

    lexer = TestLexer()

    if len(sys.argv) > 1:
        with fileinput.input() as f:
            lines = []
            for line in f:
                lines.append(line)

#            while True:
#                try:
            result = parser.parse(lexer.tokenize(''.join(lines)))
            print("{}".format(result))
#                except EOFError:
#                    break
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
