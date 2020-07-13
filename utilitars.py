
import copy
######################## -> Estrutura de dados  <- ########################
class Fila(object):
    def __init__(self):
        self.dados = []
 
    def insere(self, elemento):
        self.dados.append(elemento)
 
    def retira(self):
        return self.dados.pop(0)
 
    def vazia(self):
        return len(self.dados) == 0

class Pilha(object):
    def __init__(self):
        self.dados = []
 
    def empilha(self, elemento):
        self.dados.append(elemento)
 
    def desempilha(self):
        if not self.vazia():
            return self.dados.pop(-1)
 
    def vazia(self):
        return len(self.dados) == 0


######################## -> NodeVisitor <- ########################
class NodeVisitor(object):
    _method_cache = None

    def visit(self, node):
        """ Visit a node.
        """

        if self._method_cache is None:
            self._method_cache = {}

        visitor = self._method_cache.get(node.__class__.__name__, None)
        if visitor is None:
            method = 'visit_' + node.__class__.__name__
            visitor = getattr(self, method, self.generic_visit)
            self._method_cache[node.__class__.__name__] = visitor

        return visitor(node)
    def generic_visit(self, node):
        """ Called if no explicit visitor function exists for a
            node. Implements preorder visiting of the node.
        """
        for c in node:
            self.visit(c)

####################1#### -> SymbolTable <- ########################
class SymbolTable(object):
    '''
    Class representing a symbol table.  It should provide functionality
    for adding and looking up nodes associated with identifiers.
    '''
    def __init__(self):
        self.symtab = {}
    def lookup(self, a):
        return self.symtab.get(a)
    def add(self, a, v):
        self.symtab[a] = v

######################## -> Scope <- ########################
class Scope(object):
    '''
    Cada Scope nesse contexto contém:
        -Contém um nome. Se for uma funcão conterá o nome da função. Se for um "For", terá um identificador gerado. 
         Vale ressaltar que teremos o escopo global que exerga todos os outros   
        -Uma tabela de símbolos relacionando um id a um símbolo temporário forma %n, sendo n>=0 e positivo.
        -Uma tabela de símbolos relacionando um id a um type, como int,float etc.
        -Um conjunto de variáveis temporárias {%0,%1,%2...%n}
        -Um conjunto de variáveis {@.str.1,@.str.2,@.str.3...@.str.n} que tem como propósito tratar heaps
    '''

    def __init__(self,name='global'):
        
        self.name = name                #Nome do escopo
        self.table=SymbolTable()        #Relaciona id aos aos símbolos %n, n>=0 e inteiro
        self.table_type=SymbolTable()   #Relaciona id aos types    
        self.vars = dict()              #Variáveis do escopo
        self.vars[self.name]=0

        self.name_array=name            #Variavel que trata os heaps
        self.heaps=dict()               
    def new_temp(self):
        '''
        Create a new temporary variable of a given scope (function name).
        '''
        if self.name not in self.vars:
            self.vars[self.name] = 0
        name = "%" + "%d" % (self.vars[self.name])
        self.vars[self.name] += 1
        return name

    def new_heap(self):
        '''
        Create a new heap  of a given array .
        '''
        if self.name_array not in self.heaps:
            self.heaps[self.name_array] = 0
        name = "@.str." + "%d" % (self.heaps[self.name_array])
        self.heaps[self.name_array] += 1
        return name
    def set_name(self,name):
        self.name = name





class uCType(object):
    '''
    Class that represents a type in the uC language.  Types 
    are declared as singleton instances of this type.
    '''
    def __init__(self, typename, binary_ops=set(), unary_ops=set(),rel_ops=set(),assign_ops=set(),acept_literal=set()):
        '''
        You must implement yourself and figure out what to store.
        '''
        self.typename = typename
        self.unary_ops = unary_ops or set()
        self.binary_ops = binary_ops or set()
        self.rel_ops = rel_ops or set()
        self.assign_ops = assign_ops or set()
        self.acept_literal= acept_literal or set()

# Create specific instances of types. You will need to add
# appropriate arguments depending on your definition of uCType
intType = uCType("int",
                 unary_ops   = {"-", "+", "--", "++", "p--", "p++", "*"},
                 binary_ops  = {"+", "-", "*", "/", "%"},
                 rel_ops     = {"==", "!=", "<", ">", "<=", ">=","&&","||","&"},
                 assign_ops  = {"=", "+=", "-=", "*=", "/=", "%="},
                 acept_literal= {"int"}
                 )

floatType = uCType("float",
                 unary_ops   = {"-", "+", "--", "++", "p--", "p++", "*", "&"},
                 binary_ops  = {"+", "-", "*", "/", "%"},
                 rel_ops     = {"==", "!=", "<", ">", "<=", ">=","&&","||","&"},
                 assign_ops  = {"=", "+=", "-=", "*=", "/=", "%="},
                 acept_literal= {"int","float"}                 
                 )
charType = uCType("char",
                 binary_ops  = {"+", "-"},
                 rel_ops     = {"==", "!=","&&","||","&"},
                 assign_ops  = {"=", "+="},                 
                 acept_literal= {"char"}
    )
stringType = uCType("string",
                 binary_ops  = {"+", "-"},
                 rel_ops     = {"==", "!=","&&","||","&"},
                 assign_ops  = {"=", "+="},                 
                 acept_literal= {"char","string"}
    )
boolType = uCType("bool",
                 rel_ops     = {"==", "!=", "<", ">", "<=", ">=","&&","||","&"},                 
                 acept_literal= {"bool"}
    )

uc_types=dict()
uc_types['int'], uc_types['float'], uc_types['char'],uc_types['string'] ,uc_types['bool']= intType, floatType, charType,stringType,boolType
binary_ops  = {"+", "-", "*", "/", "%","||"}
binary_ops_visit  = {"+", "-", "*", "/", "%"}
rel_ops     = {"==", "!=", "<", ">", "<=", ">=","&&","||","&","|"}
binary=dict()
binary['+']='add'
binary['-']='sub'
binary['*']='mul'
binary['/']='div'
binary['%']='mod'
binary['<']='lt'
binary['<=']='le'
binary['>']='gt'
binary['>=']='gt'
binary['!=']='ne'
binary['&']='and'
binary['||']='or'
binary['!']='not'
binary['==']='eq'

unary=dict()
unary['--']='sub'
unary['++']='add'
unary['p++']='add'
unary['p--']='sub'
assign_op=dict()
assign_op['+=']='+'
assign_op['-=']='-'
assign_op['*=']='*'
assign_op['%=']='%'
assign_op['/=']='/'
