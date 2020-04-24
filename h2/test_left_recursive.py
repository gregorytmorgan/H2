#!/usr/bin/python3.6
#
# test_parser.py
#
# Small subset of grammar to test left recursive statement parse, line/char and error reporting, ...
#

import ast
import sys
from sly import Lexer
from sly import Parser
from simple_node import SimpleNode as Node

# print a breadcrumb for each(most) productions
Debug = False

# don't run the parser, just tokenize
Tokenize_only = False

# use with Tokenize_only
Show_endlines = True

# use with Tokenize_only
Show_comments = True


####################################
#
# Lexer
#
####################################

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
        'False',
        'Print',
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
        'DELIM',
        'TERM',
        'PRINT',
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
    DELIM       = r','
    TERM        = r'\.'

    PRINT       = r'Print'
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
#        return token

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

    def error(self, token):
        print("Line {}: Bad character '{}' at char {}".format(self.lineno, token.value[0], self.find_column(token.value[0], token)))
        self.index += 1

####################################
#
# Parser
#
####################################


    #
    # It is important that the last line/statement NOT have and an endline. Endline is a delimiter, not a terminator.
    #


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

    # default start is the first production - 'code'
    #start = "expr"
    #start = "statements"

    #
    # code
    #
    @_('statements')
    def code(self, p):
        if p.statements is None:
            return []
        else:
            return p.statements

    #
    # statements
    #

    # empty statement
    @_('empty')
    def statements(self, p):
        return None

    # left recursive statements
    @_('statements statement')
    def statements(self, p):
        if p.statements is None and p.statement is None:
            if Debug: print("statement(None) statement(None)")
            return None
        elif p.statement is None:
            if Debug : print("statements statement(None)")
            return [p.statements]
        elif p.statements is None:
            if Debug: print("statements(None) statement")
            return [p.statement]
        else:
            if Debug: print("statements statement")
            return p.statements + [p.statement]

    #
    # statement
    #

    # ENDLINE only statement - causes recursive statement list
    @_('ENDLINE')
    def statement(self, p):
        self.line_start = p.index
        self.char_adj += 1
        # return None

    # assignment statement
    @_('ID ASSIGN expr',
       'ID ASSIGN error')
    def statement(self, p):
        if Debug: print("assignment")
        self.line_start = p.index
        if hasattr(p, 'expr'):
            return Node(('='), [Node(('ID', p.ID)), p[2]])
        else:
            return Node(('error', "There was an assignment error at line {}, char {}. Token {}({})".format(p.error.lineno, p.error.index - self.line_start, p.error.type, p.error.value)))

    # print statement
    @_('PRINT LPAREN expr RPAREN',
       'PRINT LPAREN error RPAREN')
    def statement(self, p):
        if Debug: print("print")
        self.line_start = p.index
        if hasattr(p, 'expr'):
            return Node(('print'), [p[2]])
        else:
            return Node(('error', "There was a print error at line {}, char {}. Token {}({})".format(p.error.lineno, p.error.index - self.line_start, p.error.type, p.error.value)))

    #
    # expr
    #

    @_('LPAREN expr RPAREN')
    def expr(self, p):
        if hasattr(p, 'expr'):
            return p.expr

    @_('MINUS expr %prec UMINUS')
    def expr(self, p):
        return Node('uminus', [p.expr])

    # expr
    @_('NUMBER')
    def expr(self, p):
        if Debug: print("NUMBER" , p.NUMBER)
        return Node(('number', p.NUMBER))

    @_('BOOL')
    def expr(self, p):
        if Debug: print("BOOL" , p.BOOL)
        return Node(('bool', p.BOOL))

    @_('ID')
    def expr(self, p):
        if Debug: print("ID" , p.ID)
        return Node(('id', p.ID))

    @_('STRING')
    def expr(self, p):
        if Debug: print("STRING" , p.STRING)
        return Node(('string', p.STRING))

    @_('expr PLUS expr',
       'expr MINUS expr',
       'expr TIMES expr',
       'expr DIVIDE expr')  # 'expr error expr' cause 5 s/r conflicts
    def expr(self, p):
        if Debug: print("expr", p[1] , "expr")
        return Node(p[1], [p.expr0, p.expr1])

    #
    # empty
    #
    @_('')
    def empty(self, p):
        if Debug: print("empty")
        pass

#
# Parse input text and print syntax tree
#
def parse_input(results):
    lexer = Lexer()
    parser = Parser()

    if Tokenize_only:
        for tok in lexer.tokenize(results):
            if not Show_endlines and tok.type == 'ENDLINE':
                continue
            if not Show_comments and tok.type == 'COMMENT':
                continue
            print('type=%r, value=%r' % (tok.type, tok.value))
    else:
        results = parser.parse(lexer.tokenize(results))
        if (results is None) or (isinstance(results, list) and len(results) == 0):
            print('No statements')
        elif isinstance(results, list) and isinstance(results[0], Node):
            for s in results:
                print(str(s))
        else:
            print(results)

#
# main - read input from files, stdin or interactive console
#
def main():
    import fileinput

    # results generally returns a list of statements (SimpleNodes). If the parser
    # is set to start at a production other than statements, it will return a SimpleNode

    if len(sys.argv) > 1:
        with fileinput.input() as f:
            lines = []
            for line in f:
                lines.append(line)
            #parse_input(''.join(lines).strip())
            parse_input(''.join(lines))
    else:
        print("Interactive mode. Ctrl-D to exit.")
        while True:
            try:
                text = input()
                parse_input(text)
            except EOFError:
                break

if __name__ == '__main__':
    main()
