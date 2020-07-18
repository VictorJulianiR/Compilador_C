
import sys
from blocks import *

def _repr(obj):
    """
    Get the representation of an object, with dedicated pprint-like format for lists.
    """
    if isinstance(obj, list):
        return '[' + (',\n '.join((_repr(e).replace('\n', '\n ') for e in obj))) + '\n]'
    else:
        return repr(obj) 
    
class Node(object):
    """ Abstract base class for AST nodes.
    """
    gen_name=None
    type_name=None
    type_conc=None
    gen_location=None
    def __repr__(self):
        """ Generates a python representation of the current node
        """
        result = self.__class__.__name__ + '('
        indent = ''
        separator = ''
        for name in self.__slots__[:-1]:
            result += separator
            result += indent
            result += name + '=' + (_repr(getattr(self, name)).replace('\n', '\n  ' + (' ' * (len(name) + len(self.__class__.__name__)))))
            separator = ','
            indent = ' ' * len(self.__class__.__name__)
        result += indent + ')'
        return result

    def children(self):
        """ A sequence of all children that are Nodes
        """
        pass

    def show(self, buf=sys.stdout, offset=0, attrnames=False, nodenames=False, showcoord=False, _my_node_name=None):
        """ Pretty print the Node and all its attributes and children (recursively) to a buffer.
            buf:
                Open IO buffer into which the Node is printed.
            offset:
                Initial offset (amount of leading spaces)
            attrnames:
                True if you want to see the attribute names in name=value pairs. False to only see the values.
            nodenames:
                True if you want to see the actual node names within their parents.
            showcoord:
                Do you want the coordinates of each Node to be displayed.
        """
        lead = ' ' * offset
        if nodenames and _my_node_name is not None:
            buf.write(lead + self.__class__.__name__+ ' <' + _my_node_name + '>: ')
        else:
            buf.write(lead + self.__class__.__name__+ ': ')

        if self.attr_names:
            if attrnames:
                nvlist = [(n, getattr(self, n)) for n in self.attr_names if getattr(self, n) is not None]
                attrstr = ', '.join('%s=%s' % nv for nv in nvlist)
            else:
                vlist = [getattr(self, n) for n in self.attr_names]
                attrstr = ', '.join('%s' % v for v in vlist)
            buf.write(attrstr)

        if showcoord:
            if self.coord:
                buf.write('%s' % self.coord)
        buf.write('\n')

        for (child_name, child) in self.children():
            child.show(buf, offset + 4, attrnames, nodenames, showcoord, child_name)
class Coord(object):
    """ Coordinates of a syntactic element. Consists of:
            - Line number
            - (optional) column number, for the Lexer
    """
    __slots__ = ('line', 'column')

    def __init__(self, line, column=None):
        self.line = line
        self.column = column

    def __str__(self):
        if self.line:
            coord_str = "   @ %s:%s" % (self.line, self.column)
        else:
            coord_str = ""
        return coord_str



class Type(Node):
    __slots__ = ('names', 'coord')

    def __init__(self, names, coord=None):
        self.names = names
        self.coord = coord

    def children(self):
        nodelist = []
        return tuple(nodelist)

    attr_names = ('names',)
    
class Decl(Node):
    __slots__ = ('id','const','binop','vardecl','funcdecl','arraydecl','initlist','id_2', 'ptrs','arrayref','funccall','coord')

    def __init__(self, id,const=None,binop=None,vardecl=None,funcdecl=None,arraydecl=None,arrayref=None,initlist=None,id_2=None,ptrs=None,funccall=None, coord=None):
        self.id=id
        self.vardecl = vardecl
        self.const=const
        self.binop=binop
        self.funcdecl=funcdecl
        self.arraydecl=arraydecl
        self.initlist=initlist
        self.id_2=id_2
        self.ptrs=ptrs
        self.arrayref=arrayref
        self.funccall=funccall
        self.coord = coord
        

    def children(self):
        nodelist = []
        if self.vardecl is not None:
            nodelist.append(('vardecl', self.vardecl))
        
        if (self.ptrs):
            for i, child in enumerate(self.ptrs or []):
              if(child!=None):
                nodelist.append(("ptrs[%d]" % i, child))
        
        if self.funcdecl is not None:
            nodelist.append(('funcdecl', self.funcdecl))

        if self.arraydecl is not None:
            nodelist.append(('arraydecl', self.arraydecl))

        if self.const is not None:
            nodelist.append(('const', self.const))
        if self.binop is not None:
            nodelist.append(('binop', self.binop))


        if self.initlist is not None:
            nodelist.append(('initlist', self.initlist))

        if self.id_2 is not None:
            nodelist.append(('id_2', self.id_2))
        if self.arrayref:   
            nodelist.append(('arrayref', self.arrayref))
        if self.funccall:   
            nodelist.append(('funccall', self.funccall))
        
        return tuple(nodelist)

    attr_names = ('id',)

class Read(Node):
    __slots__ = ('expr', 'coord')

    def __init__(self, expr, coord=None):
        super().__init__()
        self.expr = expr
        self.coord = coord

    def children(self):
        nodelist = []
        for i, child in enumerate(self.expr or []):
            if(child!=None):
                nodelist.append(("expr[%d]" % i, child))
        return tuple(nodelist)


    attr_names = ()
class VarDecl(Node):
    __slots__ = ( 'type', 'coord')

    def __init__(self, type=None, coord=None):
        
        self.type = type
        self.coord = coord

    
    def children(self):
        nodelist = []
        if self.type is not None:
            nodelist.append(('type', self.type))
        
        return tuple(nodelist)
    attr_names = ()
############
class Print(Node):
    __slots__ = ('expr', 'coord')

    def __init__(self, expr, coord=None):
        self.expr = expr
        self.coord = coord

    def children(self):
        nodelist = []
        if self.expr is not None:
            nodelist.append(('expr', self.expr))
        return tuple(nodelist)
    attr_names = ()


class Assert(Node):
    __slots__ = ('expr', 'coord')

    def __init__(self, expr, coord=None):
        self.expr = expr
        self.coord = coord

    def children(self):
        nodelist = []
        if self.expr is not None:
            nodelist.append(('expr', self.expr))
        return tuple(nodelist)

    attr_names = ()

class GlobalDecl(Node):
    __slots__ = ('funcdef', 'gdecls', 'coord')

    def __init__(self, funcdef, gdecls, coord=None):
        self.funcdef = funcdef
        self.gdecls = gdecls
        self.coord = coord

    def children(self):
        nodelist = []
        if self.funcdef is not None:
            nodelist.append(("funcdef", self.funcdef))

        for i, child in enumerate(self.gdecls or []):
            nodelist.append(("gdecls[%d]" % i, child))
        
        return tuple(nodelist)

    attr_names = ()

class Program(Node):
    __slots__ = ('gdecls', 'coord')
    
    def __init__(self, gdecls, coord=None):
        self.gdecls = gdecls
        self.coord = coord

    def children(self):
        nodelist = []
        for i, child in enumerate(self.gdecls or []):
            nodelist.append(("gdecls[%d]" % i, child))
        return tuple(nodelist)

    attr_names = ()

class BinaryOp(Node):
    __slots__ = ('op', 'left', 'right', 'coord')
    
    def __init__(self, op, left, right, coord=None):
        self.op = op
        self.left = left
        self.right = right
        self.coord = coord

    def children(self):
        nodelist = []
        if self.left is not None: nodelist.append(("left", self.left))
        if self.right is not None: nodelist.append(("right", self.right))
        return tuple(nodelist)

    attr_names = ('op', )
    
class Constant(Node):
    __slots__ = ('type', 'value', 'coord')
    
    def __init__(self, type=None, value=None, coord=None):
        self.type = type
        self.value = value
        self.coord = coord

    def children(self):
        nodelist = []
        return tuple(nodelist)

    attr_names = ('type', 'value', )

class ArrayDecl(Node):
    __slots__ = ('type', 'dim', 'dim_quals','vardecl' ,'name','arraydecl','coord')
    def __init__(self, type=None, dim=None, dim_quals=None,vardecl=None,name=None,arraydecl=None, coord=None):
        self.type = type
        self.dim = dim
        self.dim_quals = dim_quals
        self.vardecl=vardecl
        self.name=name
        self.arraydecl=arraydecl
        self.coord = coord

    def children(self):
        nodelist = []
        if self.type is not None: nodelist.append(("type", self.type))
        if self.vardecl is not None: nodelist.append(("vardecl", self.vardecl))
        if self.dim is not None: nodelist.append(("dim", self.dim))
        if self.arraydecl is not None: nodelist.append(("arraydecl", self.arraydecl))

        
        return tuple(nodelist)

    
    attr_names = ( )

class ArrayRef(Node):
    __slots__ = ('name', 'subscript','name_id' 'coord',)
    def __init__(self, name, subscript,name_id=None, coord=None):
        self.name = name
        self.subscript = subscript
        self.name_id=name_id
        self.coord = coord
    def children(self):
        nodelist = []
        if self.name is not None: nodelist.append(("name", self.name))
        if self.subscript is not None: nodelist.append(("subscript", self.subscript))
        return tuple(nodelist)


    attr_names = ()

class Assignment(Node):
    __slots__ = ('op', 'lvalue', 'rvalue', 'coord')

    def __init__(self, op, lvalue, rvalue, coord=None):
        self.op = op
        self.lvalue = lvalue
        self.rvalue = rvalue
        self.coord = coord

    def children(self):
        nodelist = []
        if self.lvalue is not None: nodelist.append(("lvalue", self.lvalue))
        if self.rvalue is not None: nodelist.append(("rvalue", self.rvalue))
        return tuple(nodelist)

    attr_names = ('op', )
class Break(Node):
    __slots__ = ('coord')
    def __init__(self, coord=None):
        self.coord = coord

    def children(self):
        return ()


    attr_names = ()    
class Cast(Node):
    __slots__ = ('to_type', 'expr', 'coord')
    def __init__(self, to_type, expr, coord=None):
        self.to_type = to_type
        self.expr = expr
        self.coord = coord

    def children(self):
        nodelist = []
        if self.to_type is not None: nodelist.append(("to_type", self.to_type))
        if self.expr is not None: nodelist.append(("expr", self.expr))
        return tuple(nodelist)
    attr_names = ()
class Compound(Node):
    __slots__ = ('decl','st', 'coord')
    def __init__(self, decl=None,st=None, coord=None):
        if(decl!=None):
            self.decl=decl
        self.st=st
        self.coord = coord

    def children(self):
        nodelist = []
        for d in (self.decl or []):
            for i, child in enumerate(d or []):
                if(child!=None):
                    nodelist.append(("decl[%d]" % i, child))

        for i, child in enumerate(self.st or []):
            if(child!=None):
                nodelist.append(("[%d]" % i, child))    
        return tuple(nodelist)
    attr_names = ()


class DeclList(Node):
    __slots__ = ('decls', 'coord')
    def __init__(self, decls, coord=None):
        self.decls = decls
        self.coord = coord

    def children(self):
        nodelist = []
        for i, child in enumerate(self.decls or []):
            nodelist.append(("decls[%d]" % i, child))
        return tuple(nodelist)
    attr_names = ()
class EmptyStatement(Node):
    __slots__ = ('coord')
    def __init__(self, coord=None):
        self.coord = coord

    def children(self):
        return ()
class ExprList(Node):
    __slots__ = ('exprs', 'coord')
    def __init__(self, exprs, coord=None):
        self.exprs = exprs
        self.coord = coord

    def children(self):
        nodelist = []
        for i, child in enumerate(self.exprs or []):
            nodelist.append(("exprs[%d]" % i, child))
        return tuple(nodelist)
    attr_names = ()
class For(Node):
    __slots__ = ('init', 'cond', 'next', 'stmt', 'coord')
    def __init__(self, init, cond, next, stmt, coord=None):
        self.init = init
        self.cond = cond
        self.next = next
        self.stmt = stmt
        self.coord = coord

    def children(self):
        nodelist = []
        if self.init is not None: nodelist.append(("init", self.init))
        if self.cond is not None: nodelist.append(("cond", self.cond))
        if self.next is not None: nodelist.append(("next", self.next))
        if self.stmt is not None: nodelist.append(("stmt", self.stmt))
        return tuple(nodelist)
    attr_names = ()



class FuncCall(Node):
    __slots__ = ('name', 'args', 'coord')
    def __init__(self, name, args, coord=None):
        self.name = name
        self.args = args
        self.coord = coord

    def children(self):
        nodelist = []
        if self.name is not None: nodelist.append(("name", self.name))
        if self.args is not None: nodelist.append(("args", self.args))
        return tuple(nodelist)

    attr_names = ()
class FuncDecl(Node):
    
    __slots__ = ('vardecl', 'paramlist', 'name','coord')
    def __init__(self, vardecl, paramlist,name=None, coord=None):
        self.vardecl = vardecl
        self.paramlist = paramlist
        self.name=name
        self.coord = coord

    def children(self):
        nodelist = []
        if self.name is not None: nodelist.append(("name", self.name))

        if self.paramlist is not None: nodelist.append(("paramlist", self.paramlist))

        if self.vardecl is not None: nodelist.append(("vardecl", self.vardecl))
        return tuple(nodelist)
  
    attr_names = ()

class FuncDef(Node):
    #        p[0]=FuncDef(type=p[0], decl=tmp2, comp=p[4])

    __slots__ = ('decl','funcdecl','type', 'comp','cfg' ,'coord')
    def __init__(self,type, decl,comp,funcdecl=None,cfg=None, coord=None):
        self.type=type
        self.cfg=cfg
        self.decl = decl
        self.comp = comp
        self.funcdecl=funcdecl
        self.coord = coord
        self.blocks=[]
        self.begin=-1
        self.end=-1
        
    
    def children(self):
        nodelist = []
        if self.type is not None: nodelist.append(("type", self.type))
        if self.decl is not None: nodelist.append(("decl", self.decl))
        if self.funcdecl is not None: nodelist.append(("funcdecl", self.funcdecl))
        if self.comp is not None: nodelist.append(("comp", self.comp))
        return tuple(nodelist)
    def get_blocks_dfs(self,block):
        if( not isinstance(block, Block) or block.visit ):         return
        block.visit=True
        self.blocks.append(block)#Essa linha pega os blocks
        self.get_blocks_dfs(block.next_block)
        if(isinstance(block, ConditionBlock)):
            self.get_blocks_dfs(block.fall_through)
    def get_blocks_bfs(self,block):  
        fila=Fila()
        fila.insere(block)
        while(not fila.vazia()):
            block=fila.retira()
            if( isinstance(block, Block) and not block.visit ):         
                block.visit=True    
                self.blocks.append(block)
                fila.insere(block.next_block)
                if(isinstance(block, ConditionBlock)):      fila.insere(block.fall_through)
    
    
    def reset(self):
        for block in self.blocks:
            block.visit=False
    def get_begin(self):
        return self.begin
    def get_end(self):
        return self.end
    attr_names = ()

class ID(Node):
    __slots__ = ('name','type', 'coord')
    def __init__(self, name,type=None, coord=None):
        self.name = name
        self.type=type
        self.coord = coord

    def children(self):
        nodelist = []
        return tuple(nodelist)
    attr_names = ('name',)

class If(Node):
    __slots__ = ('cond', 'iftrue', 'iffalse', 'coord')
    def __init__(self, cond, iftrue, iffalse, coord=None):
        self.cond = cond
        self.iftrue = iftrue
        self.iffalse = iffalse
        self.coord = coord

    def children(self):
        nodelist = []
        if self.cond is not None: nodelist.append(("cond", self.cond))
        if self.iftrue is not None: nodelist.append(("iftrue", self.iftrue))
        if self.iffalse is not None: nodelist.append(("iffalse", self.iffalse))
        return tuple(nodelist)
    attr_names = ()

class InitList(Node):
    __slots__ = ('exprs', 'coord')
    def __init__(self, exprs, coord=None):
        self.exprs = exprs
        self.coord = coord

    def children(self):
        nodelist = []
        for i, child in enumerate(self.exprs or []):
            nodelist.append(("exprs[%d]" % i, child))
        return tuple(nodelist)

    attr_names = ()


class ParamList(Node):
    __slots__ = ('params', 'coord')
    def __init__(self, params, coord=None):
        self.params = params
        self.coord = coord

    def children(self):
        nodelist = []
        for i, child in enumerate(self.params or []):
            nodelist.append(("params[%d]" % i, child))
        return tuple(nodelist)

    
    attr_names = ()


class Constant(Node):
    __slots__ = ('type', 'value', 'coord')
    def __init__(self, type, value, coord=None):
        self.type = type
        self.value = value
        self.coord = coord

    def children(self):
        nodelist = []
        return tuple(nodelist)

    def __iter__(self):
        return
        yield

    attr_names = ('type', 'value', )
class PtrDecl(Node):
    __slots__ = ('p', 'type', 'coord')
    def __init__(self, p=None, type=None, coord=None):
        self.p = p
        self.type = type
        self.coord = coord

    def children(self):
        nodelist = []
        if self.type is not None: nodelist.append(("type", self.type))
        return tuple(nodelist)
    attr_names = ('p', )


class Return(Node):
    __slots__ = ('expr', 'coord')
    def __init__(self, expr, coord=None):
        self.expr = expr
        self.coord = coord

    def children(self):
        nodelist = []
        if self.expr is not None: nodelist.append(("expr", self.expr))
        return tuple(nodelist)

    attr_names = ()


class UnaryOp(Node):
    __slots__ = ('op', 'left','right', 'coord')
    def __init__(self, op, left,right=None, coord=None):
        self.op = op
        self.left = left
        self.right = right
        self.coord = coord

    def children(self):
        nodelist = []
        if self.left is not None: nodelist.append(("left", self.left))
        return tuple(nodelist)
    attr_names = ('op', )

class While(Node):
    __slots__ = ('cond', 'stmt', 'coord')
    def __init__(self, cond, stmt, coord=None):
        self.cond = cond
        self.stmt = stmt
        self.coord = coord

    def children(self):
        nodelist = []
        if self.cond is not None: nodelist.append(("cond", self.cond))
        if self.stmt is not None: nodelist.append(("stmt", self.stmt))
        return tuple(nodelist)

    attr_names = ()



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
    def top(self):
        if not self.vazia():
            return self.dados[-1]
    def penultimo(self):
        if  len(self.dados)>1:
            return self.dados[-2]

 
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
        self.vars[self.name]=1
        self.retorno=[]
        self.name_array=name            #Variavel que trata os heaps
        self.param_list=[]      
    def new_temp(self):
        '''
        Create a new temporary variable of a given scope (function name).
        '''
        if self.name not in self.vars:
            self.vars[self.name] = 1
        name = "%" + "%d" % (self.vars[self.name])
        self.vars[self.name] += 1
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
binary['>=']='gq'
binary['!=']='ne'
binary['&']='and'
binary['||']='or'
binary['!']='not'
binary['==']='eq'
binary['&&']='and'



unary={ '--'    :   'sub',
        '++'    :   'add',
        'p++'   :   'add',
        'p--'   :   'sub',
        '&'     :   'get'
        }
assign_op=dict()
assign_op['+=']='+'
assign_op['-=']='-'
assign_op['*=']='*'
assign_op['%=']='%'
assign_op['/=']='/'
