

import lexer
from ply import yacc
from ast import *
from lexer import UCLexer
import ply


class UCParser(object):
    
    #('left','LPAREN','RPAREN')
    precedence = (
        
        ('left', 'OR'),
        ('left', 'AND'),
        ('left','ADDRESS'),
        ('left', 'EQ', 'DIF'),
        ('left','BT', 'BQ','LT', 'LQ'),
        ('left','PLUS','MINUS'),
        ('left','TIMES','DIVIDE',"RES")
            )


    def __init__(self): #Construtor da classe.
        self.lexer = UCLexer(lexer.print_error)
        self.lexer.build()
        self.tokens = self.lexer.tokens
        self.parser = yacc.yacc(module=self)
        #parser = yacc.yacc(module=self)
    #
    def parse(self, text, filename='', debuglevel=0):
        """ Parses C code and returns an AST.
            text:
                A string containing the C source code
            filename:
                Name of the file being parsed (for meaningful
                error messages)
            debuglevel:
                Debug level to yacc
        """
        self.lexer.filename = filename
        self.lexer.reset_lineno()
        #self._scope_stack = [dict()]
        #self._last_yielded_token = None
        return self.parser.parse(
                input=text,
                lexer=self.lexer,
                debug=debuglevel)

    
    def _token_coord(self, p, token_idx,type=None):
        last_cr = p.lexer.lexer.lexdata.rfind('\n', 0, p.lexpos(token_idx))
        if last_cr < 0:
            last_cr = -1
            
        column = (p.lexpos(token_idx) - (last_cr))
        '''if(isinstance(type,Compound)):
            column=1
        '''
        return Coord(p.lineno(token_idx), column)

    
    #
    def p_program(self,p):
        """ program  : global_declaration_list
        """
        p[0]=Program(p[1], coord=self._token_coord(p,1))

    #
    def p_global_declaration_list(self, p):
        """ global_declaration_list : global_declaration
                                    | global_declaration_list global_declaration
        """

        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0]=p[1]+[p[2]]
    
    #*
    def p_global_declaration(self,p):
        '''global_declaration  : function_definition
        '''
        p[0]=p[1]
    #*
    def p_global_declaration_1(self,p):
        '''global_declaration  : declaration
          '''
        p[0] = GlobalDecl(funcdef=None, gdecls=p[1],coord=self._token_coord(p,1))

    def p_function_definition(self,p):
        '''function_definition : type_specifier declarator declaration_list compound_statement
                               |  declarator declaration_list compound_statement
        '''
        
        #falta o ID
        if(len(p)==5):
            if(isinstance(p[2],tuple)):
                tmp1=Decl(id=p[2][1].name,funcdecl=p[2][1])
                p[2][1].vardecl.type=p[1]
                p[0]=FuncDef(type=p[1], decl=tmp1, comp=p[4],coord=self._token_coord(p,1))
               
            else:
                tmp1=Decl(id=p[2].name,funcdecl=p[2])
                p[2].vardecl.type=p[1]
                p[0]=FuncDef(type=p[1], decl=tmp1, comp=p[4],coord=self._token_coord(p,1))
                
        else:
            if(isinstance(p[1],tuple)):
                tmp1=Decl(id=p[1][1].name,funcdecl=p[1][1])
                p[0]=FuncDef(type=None,decl=tmp1, comp=p[3],coord=self._token_coord(p,1))
            else:
                tmp1=Decl(id=p[1].name,funcdecl=p[1])
                p[0]=FuncDef(type=None,decl=tmp1, comp=p[3],coord=self._token_coord(p,1))
                
        
    #
    def p_declaration_list(self,p):
        '''declaration_list : declaration
                            | declaration declaration_list
                            | empty
        ''' 
        if(len(p)==2):
            p[0]=[p[1]]
            
        else:
            p[0]=[p[1]]+p[2]

    #
    def p_type_specifier(self,p):
        '''type_specifier : VOID
                          | CHAR
                          | INT
                          | FLOAT
        '''
        p[0] = Type(p[1],coord=self._token_coord(p,1))
        

    #########
    def p_declarator(self,p):
        '''declarator : pointer direct_declarator
                      | direct_declarator
        '''
        if len(p) == 2:
            arr = p[1]
        else:
            arr = (p[1],p[2])
        p[0]=arr

        
    #    
    def p_pointer(self,p):
        '''pointer : TIMES
                   | TIMES pointer
        '''
        if len(p) == 2:
            
            p[0] = [PtrDecl(type=None ,p=p[1],coord=self._token_coord(p,1))]
            
        else:
            p[2].append(PtrDecl(type=None ,p=p[1],coord=self._token_coord(p,1)))
            
            p[0] = p[2]


    #*
    def p_direct_declarator(self,p): 
        '''direct_declarator : identifier
                             | LPAREN declarator RPAREN
                             | direct_declarator LBRACKET constant_expression_op RBRACKET
                                                
        '''
        if(len(p)==2):

            p[0] = p[1]
        elif(len(p)==3):
            p[0]=p[2]
        else:
            tmp1=None
            tmp2=VarDecl(type=None)
            if(isinstance(p[1],ID)):
                tmp1=p[1]
                p[0] = ArrayDecl(type=None,dim=p[3],vardecl=tmp2,name=tmp1,coord=self._token_coord(p,1))
                
            elif(isinstance(p[1],ArrayDecl)):
                tmp1=p[1].name
                aux=p[1]
                while(aux.arraydecl):
                    aux=aux.arraydecl                 
                aux.arraydecl = ArrayDecl(type=None,dim=p[3],vardecl=tmp2,name=tmp1,coord=self._token_coord(p,1))
                p[0]=p[1]

                
     
    def p_constant_expression_op(self,p):
        '''
        constant_expression_op : constant_expression
                               | empty
        '''
        p[0]=p[1]
    def p_direct_declarator_1(self,p):
        '''
        direct_declarator : direct_declarator LPAREN parameter_list RPAREN
        '''
        arr = FuncDecl(
            vardecl=VarDecl(type=None),
            paramlist=p[3],
            coord=self._token_coord(p,1),
            name=p[1]
        )

        p[0] = arr
    def p_direct_declarator_2(self,p):
        ''' direct_declarator : direct_declarator LPAREN identifier_list RPAREN
        '''
        if(isinstance(p[1],ID) ):

            arr = FuncDecl(
            vardecl=VarDecl(type=None,coord=self._token_coord(p,1)),
            paramlist=None,
            coord=None,
            name=p[1]
            )
        p[0]=arr

    def p_identifier_list(self,p):
        '''identifier_list : identifier
                           | empty 
                           | identifier identifier_list
        '''
        p[0] = [p[1]] if len(p) == 2 else [p[1]] + p[2]  

    #
    def p_identifier(self, p):
        """ 
        identifier : ID
        """
        p[0] = ID(name=p[1],coord=self._token_coord(p,1))
    #
    def p_constant_expression(self,p):
        '''constant_expression : binary_expression
        '''
        p[0]=p[1]
    #
    def p_binary_expression(self,p):
        ''' binary_expression : cast_expression
                              | binary_expression   TIMES    binary_expression
                              | binary_expression  DIVIDE   binary_expression
                              | binary_expression  RES   binary_expression
                              | binary_expression  PLUS   binary_expression
                              | binary_expression  MINUS   binary_expression
                              | binary_expression  LT   binary_expression
                              | binary_expression  LQ  binary_expression
                              | binary_expression  BT   binary_expression
                              | binary_expression  BQ  binary_expression
                              | binary_expression  EQ  binary_expression
                              | binary_expression  DIF  binary_expression
                              | binary_expression  AND  binary_expression
                              | binary_expression  OR  binary_expression

        '''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = BinaryOp(p[2], p[1], p[3],coord=p[1].coord)
    #
    def p_cast_expression(self,p):
        '''cast_expression : unary_expression
                           | LPAREN type_specifier RPAREN cast_expression
        '''
        if(len(p)==2):
            p[0]=p[1]
        else:
            p[0] = Cast(p[2], p[4], coord=self._token_coord(p,1))

    #
    def p_unary_expression(self,p):    
        '''unary_expression : postfix_expression
                            | PLUSPLUS unary_expression
                            | MINUSMINUS unary_expression
                            | unary_operator cast_expression
        '''
        if(len(p)==2):
            p[0]=p[1]
        else:
            if(p[1]=='++' or p[1]=='--'):
                p[0] = UnaryOp(p[1], left=p[2],right=Constant(type='int',value=1), coord=p[2].coord )
            else:
                p[0] = UnaryOp(p[1], left=p[2],right=None, coord=p[2].coord )

    #
    def p_postfix_expression(self,p):
        '''postfix_expression : primary_expression
                              | postfix_expression LPAREN argument_expression RPAREN
                              | postfix_expression LPAREN RPAREN
                              | postfix_expression PLUSPLUS
                              | postfix_expression MINUSMINUS
        '''
    
        if(len(p)==2):
            p[0]=p[1]
        elif(len(p)==3):
            p[0] = UnaryOp( 'p'+p[2], left=p[1], right=Constant(type='int',value=1) , coord=p[1].coord )
        elif(len(p)==5):
            p[0] = FuncCall(p[1], p[3], coord=p[1].coord)
        else:
            p[0] = FuncCall(p[1], None,coord=p[1].coord)
    def p_postfix_expression_1(self,p):
        '''
        postfix_expression : postfix_expression LBRACKET expression RBRACKET
        '''
        p[0] = ArrayRef(name=p[1],subscript=p[3], coord=p[1].coord)

    #
    def p_primary_expression(self,p):
        '''primary_expression : identifier
                              | constant
                              | LPAREN expression RPAREN
        '''
        if(len(p)==2):

            p[0]=p[1]
        else:
            p[0]=p[2]
    def p_primary_expression_1(self,p):
        '''
        primary_expression : STRING
        '''
        p[0] = Constant('string' , p[1], coord=self._token_coord(p,1))
        
    def p_constant(self,p):
        ''' 
        constant : INT_CONST         
        '''
        p[0] = Constant('int' , int(p[1]), coord=self._token_coord(p,1))

    
    def p_constant_1(self,p):
        ''' 
        constant : FLOAT_CONST
        '''
        p[0] = Constant('float' , float(p[1]), coord=self._token_coord(p,1))
    

    
        
#
    def p_constant_2(self,p):
        '''
        constant : CHAR_CONST
        '''
        p[0]=p[0] = Constant('char' , p[1], coord=self._token_coord(p,1))

    
    def p_expression(self,p):
        ''' expression  : assignment_expression
                        | expression COMMA assignment_expression
        '''
        if len(p) == 2:
            p[0] = p[1]
        else:
            if not isinstance(p[1], ExprList):
                p[1] = ExprList([p[1]],coord=p[1].coord)

            p[1].exprs.append(p[3])
            p[0] = p[1]
    #
    def p_argument_expression(self,p): 
        ''' argument_expression : assignment_expression
                                | argument_expression COMMA assignment_expression
        '''
        if len(p) == 2:
            p[0] = ExprList([p[1]], coord=p[1].coord)
        else:
            p[1].exprs.append(p[3])
            p[0] = p[1]
    #
    def p_assignment_expression(self,p): 
        ''' assignment_expression : binary_expression
                                  | unary_expression assignment_operator assignment_expression
        '''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = Assignment(p[2], p[1], p[3], coord=p[1].coord)
   #
    def p_assignment_operator(self,p):
        ''' assignment_operator : EQUALS
                                | TIMESEQUALS
                                | DIVIDEEQUALS
                                | RESEQUALS
                                | PLUSEQUALS
                                | MINUSEQUALS

        '''
        p[0] = p[1]
    #
    def p_unary_operator(self,p):
        ''' unary_operator : ADDRESS
                           | TIMES
                           | PLUS
                           | MINUS
                           | NOT
        '''
        p[0]=p[1]
    #
    def p_parameter_list(self,p):
        ''' parameter_list : parameter_declaration
                           | parameter_list COMMA parameter_declaration
        '''
        if len(p) == 2: 
            tupla=p[1]

            if(isinstance(tupla['decl'],ID)):
                tmp1=Decl(id=tupla['decl'],vardecl=VarDecl(type=tupla['type']), coord=self._token_coord(p,1))
                p[0] = ParamList([tmp1], coord=None)
        else:
            tupla=p[3]
            if(isinstance(tupla['decl'],ID)):
                tmp1=Decl(id=tupla['decl'],vardecl=VarDecl(type=tupla['type']), coord=self._token_coord(p,1))
                p[1].params.append(tmp1)
                p[0] = p[1]
    #*
    def p_parameter_declaration(self,p):
        ''' parameter_declaration : type_specifier declarator
        '''
        p[0] = dict(type=p[1],decl=p[2])

    
    def p_declaration(self,p):
        '''
        declaration :  type_specifier init_declarator_list SEMI
                    |  type_specifier SEMI
        '''     
        arr=[]
        for dic in p[2]:
            
            tmp=12*[None]
            aux1=dic['decl']
            aux2=dic['init']
            tmp[0]=VarDecl( type=p[1], coord=None)

            if(isinstance( aux1,tuple) and aux2==None):
                #int *a;
                tmp[9]=aux1[0]
                tmp[1]=aux1[1]
                aux1[1].type=p[1]
                for i in tmp[9]:
                    aux1[1].type.names=f'{aux1[1].type.names}_*'



            else:
                
                if( isinstance(aux1,ID) and aux2==None ):
                    #Do tipo int a;
                    tmp[1]=aux1
                    tmp[2]=aux2
                    aux1.type=p[1]
                elif( isinstance(aux1,ID) and isinstance(aux2,ID) ):
                    #Temos o tipo type x=b;
                    tmp[1]=aux1
                    tmp[2]=aux2
                    aux1.type=p[1]
                elif(isinstance(aux1,ID) and isinstance(aux2,Constant)): 
                    #Temos o tipo type x=1;
                    tmp[1]=aux1
                    tmp[3]= aux2
                    tmp[3].type=p[1].names 
                    aux1.type=p[1]   
                elif(isinstance(aux1,ID) and isinstance(aux2,BinaryOp)):
                    #Temos o tipo type x=a+5
                    tmp[1]=aux1
                    tmp[4]=aux2
                    aux1.type=p[1]

                elif(isinstance(aux1,ArrayDecl) and isinstance(aux2,InitList)):
                    #Temos o tipo type A[]={1,2,3}

                    aux1.vardecl.type=p[1]
                    tmp[1]=aux1.name
                    aux1.name.type=p[1]
                    tmp[5]=aux1
                    tmp[6]=aux2
                    tmp[7]=None
                elif(isinstance(aux1,ArrayDecl) and isinstance(aux2,Constant)):
                    #tipo Array char
                    aux1.vardecl.type=p[1]
                    tmp[1]=aux1.name
                    aux1.name.type=p[1]    
                    tmp[5]=aux1
                    tmp[3]=aux2
                elif(isinstance(aux1,ID) and isinstance(aux2,FuncCall)):
                    tmp[1]=aux1
                    aux1.type=p[1]
                    tmp[11]=aux2
                elif(isinstance(aux1,ArrayDecl) and isinstance(aux2,BinaryOp)):
                    aux1.vardecl.type=p[1]
                    tmp[1]=aux1.name
                    aux1.name.type=p[1]    

                    tmp[5]=aux1
                    tmp[4]=aux2
                elif(isinstance(aux1,ArrayDecl)):
                    #Declaração do tipo type a[];
                    aux1.vardecl.type=p[1]
                    tmp[1]=aux1.name
                    aux1.name.type=p[1]  
                    tmp[5]=aux1
                elif(isinstance(aux1,ID) and isinstance(aux2,ArrayRef) ):
                    tmp[1]=aux1
                    aux1.type=p[1]
                    tmp[10]=aux2

                else:
                    nada=True                  
            tmp[8]=Decl(id=tmp[1],const=tmp[3],vardecl=tmp[0],arraydecl=tmp[5],arrayref=tmp[10],initlist=tmp[6],id_2=tmp[2] ,ptrs=tmp[9],binop=tmp[4],funccall=tmp[11] ,coord=self._token_coord(p,1))
            arr.append(tmp[8])
        
        p[0]=arr
        
        #(self, name, quals, storage, funcspec, type, init, bitsize, coord=None)
        # def __init__(self, declname, type, coord=None):

    #
    def p_init_declarator_list(self,p):
        ''' init_declarator_list : init_declarator
                                 | init_declarator_list COMMA init_declarator
        '''
        p[0] = p[1] + [p[3]] if len(p) == 4 else [p[1]]
        
    #
    def p_init_declarator(self,p):
        '''init_declarator : declarator
                           | declarator EQUALS initializer
        '''
        p[0] = dict(decl=p[1], init=(p[3] if len(p) > 2 else None))

    #
    def p_initializer(self,p):
        '''initializer : assignment_expression
                       | LBRACE initializer_list RBRACE
                       | LBRACE initializer_list COMMA RBRACE
        '''
        if len(p)==2 :
            p[0]=p[1]
            
        elif(len(p)==3):
            p[0]=p[2]
        else:
           
            p[0]=p[2]
    def p_initializer_list(self,p):
        '''
        initializer_list : initializer
                         | initializer_list COMMA initializer
        '''
        if len(p) == 2:
            p[0] = InitList(exprs=[p[1]] ,coord=p[1].coord)
            
        else:
            p[1].exprs.append(p[3])
            
            p[0] = p[1]

    #*
    def p_compound_statement(self,p):
        '''
            compound_statement : LBRACE declaration_list statement_list RBRACE 
        '''
        p[0]=Compound(decl=p[2],st=p[3],coord=self._token_coord(p,1,type=Compound()))
        
    #

    def p_statement_list(self,p):
        '''
            statement_list   : statement
                             | empty 
                             | statement statement_list
        '''
        p[0] = [p[1]] if len(p) == 2 else [p[1]] + p[2]  

    #*
    def p_statement(self,p):
        '''
            statement   : expression_statement
                        | compound_statement
                        | selection_statement
                        | iteration_statement
                        | jump_statement
                        | assert_statement
                        | print_statement
                        | read_statement
        '''
        p[0]=p[1]
    #*
    def p_expression_statement(self,p):
        '''
        expression_statement : expression SEMI
                             | SEMI
        '''
        if len(p) == 2:
            p[0] = ()
        else:
            p[0] = p[1]
    def p_selection_statement(self,p):
        '''   
        selection_statement : IF LPAREN expression RPAREN statement
                            | IF LPAREN expression RPAREN statement ELSE statement
        '''
        if len(p) == 6:
            p[0] = If( cond=p[3], iftrue=p[5], iffalse=None, coord=self._token_coord(p,1))
        else:
            p[0] = If( cond=p[3], iftrue=p[5], iffalse=p[7], coord=self._token_coord(p,1))
    #*
    def p_iteration_statement(self,p):
        '''
            iteration_statement : WHILE LPAREN expression RPAREN statement
                                | FOR LPAREN expression_bin SEMI expression_bin SEMI expression_bin RPAREN statement
                                | FOR LPAREN declaration expression_bin SEMI expression_bin RPAREN statement
        '''
        
        if(len(p)==6):
            p[0]=While(cond=p[3], stmt=p[5], coord=self._token_coord(p,1))
        elif len(p) == 10:   
            p[0]=For(init=p[3], cond=p[5], next=p[7], stmt=p[9], coord=self._token_coord(p,1))
            
        else:
            p[0]=For(init=DeclList(decls=p[3], coord=self._token_coord(p,1)), cond=p[4], next=p[6], stmt=p[8], coord=self._token_coord(p,1))
            
    #
    def p_expression_bin(self,p):
        '''
            expression_bin : expression
                           | empty
        '''
        p[0]=p[1]
    #*
    def p_jump_statement(self,p):
        '''
        jump_statement : BREAK SEMI
                       | RETURN expression_bin SEMI
        '''
        
        if len(p) == 3:
            p[0] = Break(coord=self._token_coord(p,1))
        else: 
            p[0] = Return(expr=p[2], coord=self._token_coord(p,1))

    #*
    def p_assert_statement(self,p):
        '''
        assert_statement : ASSERT expression SEMI
        '''
        p[0] =  Assert(expr=p[2], coord=self._token_coord(p,1))
    #*
    def p_print_statement(self,p): 
        '''
            print_statement : PRINT LPAREN expression_bin RPAREN SEMI
        '''
        p[0]=Print(expr=p[3], coord=self._token_coord(p,1))
            
    #*    
    def p_read_statement(self,p):
        '''
        read_statement : READ LPAREN argument_expression RPAREN SEMI
        '''
        arr=[p[3]]
        if(isinstance(p[3],ExprList) and len(p[3].exprs)==1):
            arr=p[3].exprs

        p[0] =  Read(expr=arr, coord=self._token_coord(p,1))
    def p_empty(self,p):
        '''empty :'''
        pass
    
    def p_error(self, p):
        if p:
            print("Error near the symbol %s" % p.value)
        else:
            print("Error at the end of input")
    # Build the parser
    

if __name__ == '__main__':

    l=lexer.UCLexer(lexer0.print_error)
    l.build()
    tokens=l.tokens
    parser=yacc.yacc()
    while True:
        try:
            s = input()
        except EOFError:
            break
        if not s: continue
        result = parser.parse(s)
        print(result)

