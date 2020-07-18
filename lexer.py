import ply.lex as lex
from ply.lex import TOKEN


class UCLexer(object):
    """ A lexer for the uC language. After building it, set the
        input text with input(), and call token() to get new
        tokens.
    """
    def __init__(self, error_func):
        """ Create a new Lexer.
            An error function. Will be called with an error
            message, line and column as arguments, in case of
            an error during lexing.
        """
        self.error_func = error_func
        self.filename = ''

        # Keeps track of the last token returned from self.token()
        self.last_token = None

    def build(self, **kwargs):
        """ Builds the lexer from the specification. Must be
            called after the lexer object is created.

            This method exists separately, because the PLY
            manual warns against calling lex.lex inside __init__
        """
        self.lexer = lex.lex(object=self, **kwargs)

    def reset_lineno(self):
        """ Resets the internal line number counter of the lexer.
        """
        self.lexer.lineno = 1

    def input(self, text):
        self.lexer.input(text)

    def token(self):
        self.last_token = self.lexer.token()
        return self.last_token

    def find_tok_column(self, token):
        """ Find the column of the token in its line.
        """
        last_cr = self.lexer.lexdata.rfind('\n', 0, token.lexpos)
        return token.lexpos - last_cr

    # Internal auxiliary methods
    def _error(self, msg, token):
        location = self._make_tok_location(token)
        self.error_func(msg, location[0], location[1])
        self.lexer.skip(1)

    def _make_tok_location(self, token):
        return (token.lineno, self.find_tok_column(token))

    # Reserved keywords
    keywords = (
            'ASSERT', 'BREAK', 'CHAR', 'ELSE', 'FLOAT', 'FOR', 'IF',
            'INT', 'PRINT', 'READ', 'RETURN', 'VOID', 'WHILE',
        )

    keyword_map = {}
    for keyword in keywords:
        keyword_map[keyword.lower()] = keyword

    #
    # All the tokens recognized by the lexer
    #
    tokens = keywords + (
        # Identifiers
        'ID',

        # constants
        'FLOAT_CONST','INT_CONST','CHAR_CONST','STRING',

        'MINUS','PLUS','TIMES','DIVIDE','LPAREN','RPAREN',
        'SEMI', 'EQUALS','EQ','LBRACE','RBRACE','COMMA','LBRACKET','RBRACKET', 'ADDRESS','LT','LQ','BT','BQ','DIF','OR','AND','RES'
        ,'NOT','PLUSPLUS','MINUSMINUS','TIMESEQUALS', 'DIVIDEEQUALS',
        'RESEQUALS','PLUSEQUALS','MINUSEQUALS'
    )
    # Rules
    t_RESEQUALS   = r'\%\='
    t_TIMESEQUALS     = r'\*\='
    t_DIVIDEEQUALS          = r'\/\='
    t_PLUSEQUALS         = r'\+\='
    t_MINUSEQUALS        = r'\-\='
    t_PLUSPLUS   = r'\+\+'
    t_MINUSMINUS = r'\-\-'
    t_RES     =r'\%'
    t_AND     =r'\&\&'
    t_OR      =r'\|\|'
    t_DIF     = r'\!\='
    t_BT      = r'\>'
    t_BQ      = r'\>\='
    t_LQ      = r'\<\='
    t_LT      = r'\<'
    t_ADDRESS = r'\&'
    t_LBRACKET =r'\['
    t_RBRACKET =r'\]'
    t_COMMA      = r'\,'

    t_INT_CONST = r'\d+'
    t_FLOAT_CONST=r'([0-9]+([.][0-9]*)|[.][0-9]+)'



    

    t_EQ      = r'==' 
    t_EQUALS  = r'\='
    t_SEMI    = r'\;'
    t_PLUS    = r'\+'
    t_MINUS   = r'-'
    t_TIMES   = r'\*'
    t_DIVIDE  = r'\/'
    t_LPAREN  = r'\('
    t_RPAREN  = r'\)'
    t_LBRACE  = r'\{'
    t_RBRACE  = r'\}'
    t_NOT     = r'\!'
    t_ignore = ' \t'

    # Newlines
    def t_CHAR_CONST(self,t):
        r'\'.{1}\''
        t.type=self.keyword_map.get(t.value, "CHAR_CONST")
        return t
    def t_STRING(self,t):
        r'\"(.*?)\"'
        t.type=self.keyword_map.get(t.value, "STRING")
        return t
    def t_NEWLINE(self, t):
        r'\n+'
        t.lexer.lineno += t.value.count("\n")

    def t_ID(self, t):
        r'[a-zA-Z_][0-9a-zA-Z_]*'
        t.type = self.keyword_map.get(t.value, "ID")
        return t

    def t_comment(self, t):
        r'(/\*(.|\n)*?\*/) |(//.*\n)'
        t.lexer.lineno += t.value.count('\n')



    def t_error(self, t):
        msg = "Illegal character %s" % repr(t.value[0])
        self._error(msg, t)

    # Scanner (used only for test)
    def scan(self, data):
        self.lexer.input(data)
        while True:
            tok = self.lexer.token()
            if not tok:
                break
            print(tok)
def print_error(msg, x, y):
        print("Lexical error: %s at %d:%d" % (msg, x, y))

if __name__ == '__main__':
    import sys    
    m = UCLexer(print_error)
    m.build()  # Build the lexer
    m.scan(open(sys.argv[1]).read())  # print tokens
