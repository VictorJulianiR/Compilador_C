from ast import *
import copy
class Visitor(NodeVisitor):
    '''
    Program visitor class. This class uses the visitor pattern. You need to define methods
    of the form visit_NodeName() for each kind of AST node that you want to process.
    Note: You will need to adjust the names of the AST nodes if you picked different names.
    '''
    def __init__(self):
        # Initialize the symbol table
        self.scope_current=None
        self.scopes=dict()

        self.symtab = SymbolTable()
        self.stk_sco=Pilha()
        #self.debug = debug


        # Add built-in type names (int, float, char) to the symbol table
        '''self.symtab.add("int",uctype.int_type)
        self.symtab.add("float",uctype.float_type)
        self.symtab.add("char",uctype.char_type)
        '''

    def visit_Program(self,node):
        # 1. Visit all of the global declarations
        # 2. Record the associated symbol table
        self.scopes['global']=Scope()

        for _decl in node.gdecls:
            self.scope_current=self.scopes.get('global')
            self.visit(_decl)

    def visit_GlobalDecl(self, node):     
        self.assert_declarations(node.gdecls)
    def visit_FuncDef(self, node):
        name=node.decl.id.name
        escopo=copy.deepcopy(self.scope_current)
        escopo.set_name(name)
        self.scope_current=escopo
        self.scopes[name]=escopo
        
        params=[]
        if(node.decl.funcdecl.paramlist):      
            params=node.decl.funcdecl.paramlist.params
            self.assert_declarations(params)

        
        tam_arg=len(params)
        type_func=node.type.names
        inf=(type_func,tam_arg)
        escopo.table.add(name,inf)
        escopo.table_type.add(name,type_func)
        self.scopes.get('global').table.add(name,inf)
        self.scopes.get('global').table_type.add(name,type_func)


        if(node.comp):
            self.visit(node.comp)
    def visit_FuncCall(self,node):
        name=node.name.name
        inf=self.scopes.get('global').table.lookup(name)
        node.type_name=inf[0]
        if(node.args):
            assert len(node.args.exprs)==inf[1], f'Function parameters require: {inf[1]}, but you have passed: {len(node.args.exprs)} on line {node.coord.line} column {node.coord.column}'
        

    def visit_Compound(self,node):
        if(node.decl[0]):
            for decls in node.decl:
                self.assert_declarations(decls)

        if(node.st[0]):
            for no in node.st:
                self.visit(no)
    def visit_Assert(self,node):
        self.visit(node.expr)

    def visit_Assignment(self, node):
        self.visit(node.lvalue)
        self.visit(node.rvalue)

    
        if(isinstance(node.lvalue,ArrayRef)):   
            deep1=self.deep_arrayRef(node.lvalue)
            decl=self.scope_current.table.lookup(node.lvalue.name_id.name.name)

            deep2=self.deep_arrayDecl(decl.arraydecl)
        
            assert deep1==deep2,f'Array Indexing not exist on line {node.lvalue.coord.line} '
        if(isinstance(node.rvalue,ArrayRef)):  
            deep1=self.deep_arrayRef(node.rvalue)
            decl=self.scope_current.table.lookup(node.rvalue.name_id.name)
            deep2=self.deep_arrayDecl(decl.arraydecl)

            assert deep1==deep2,f'Indexing not exist on line {node.lvalue.coord.line} '''
        
        assert node.op in uc_types.get(node.lvalue.type_name).assign_ops,f' Operador assignment {node.op} not accept '
        assert node.lvalue.type_name == node.rvalue.type_name, "Type mismatch in assignment"

    
    def deep_arrayRef(self,node):
        if(node.name and isinstance(node.name,ArrayRef)):
            return self.deep_arrayRef(node.name)+1
        else:
            return 1
    
    def deep_arrayDecl(self,node):
        if(node and node.arraydecl):
            return self.deep_arrayDecl(node.arraydecl)+1
        else:
            return 1
    def visit_If(self,node):
        self.visit(node.cond)
        self.visit(node.iftrue)
        if (node.iffalse):  self.visit(node.iffalse)

    def visit_Return(self,node):
        type=None
        if(node.expr):  
            self.visit(node.expr)
            type=node.expr.type_name
        name_func=self.scope_current.name
        type_rt=self.scope_current.table_type.lookup(name_func)
        if(type_rt=='void'):    type_rt=None
        assert type_rt==type, f'Function must return {type_rt}, but returned {type} on line {node.coord.line} column {node.coord.column}'
    def visit_Read(self,node):
        self.visit(node.expr)
    def visit_ExprList(self,node):
        for no  in node.exprs:
            self.visit(no)
    def assert_declarations(self, node):
        escopo=self.scope_current
        for decl in node:
            name_id=decl.id.name
            type=decl.vardecl.type.names
            escopo.table_type.add(name_id,type)
            escopo.table.add(name_id,decl)
            self.visit(decl.id)  
                      

            if(decl.arraydecl and decl.const):
                #char a[]="string";
                if(decl.arraydecl.dim):
                    assert decl.arraydecl.dim.value+2==len(decl.const.value),"// Error (size mismatch on initialization)"
                
            elif(decl.const):
                value=decl.const.value
                what=self.isWhat(value)
                assert what in uc_types.get(type).acept_literal  ,f"// Error (canot assign {what} to {type})"
            
                
                #int x=1;
            elif(decl.binop):
                self.visit(decl.binop)
                assert decl.binop.type_name == decl.id.type_name, "Type mismatch in assignment"
            elif(decl.arrayref):
                #Tratar
                self.visit(decl.arrayref)
                assert decl.arrayref.type_name == decl.id.type_name, "Type mismatch in assignment"
            elif(decl.funccall):
                #Tratar
                self.visit(decl.funccall)
                assert decl.funccall.type_name == decl.id.type_name, "Type mismatch in assignment"       
            elif(decl.arraydecl):
                #Todas as declarações de arrays
                type=decl.vardecl.type.names
                self.treat_array(type,decl.arraydecl,decl.initlist)                    
                
                #int x[2];
            elif(decl.ptrs):
                nada=True
                part=f'{decl.vardecl.type.names}'
                
            elif(decl.id_2):
                self.visit(decl.id_2)
                assert decl.id_2.type_name == decl.id.type_name, "Type mismatch in assignment"
    
            else:
                nada=True
                #int x[];
    
                    
    def visit_While(self,node):
        self.visit(node.cond)
        assert node.cond.type_name=='bool',f'Condition is not the type boolean on line {node.coord.line} column {node.coord.column}'
        self.visit(node.stmt)
        
    def visit_Break(self,node):
        pass
    def visit_Cast(self,node):
        self.visit(node.to_type)
        self.visit(node.expr)
        node.type_name=node.to_type.type_name
    def visit_Type(self,node):
        node.type_name=node.names
        
    def visit_For(self,node):
        self.stk_sco.empilha(self.scope_current)
        escopo=copy.deepcopy(self.scope_current)#Cria um novo escopo cópia, assim ele pode enxergar fora e dentro
        self.scope_current=escopo
        if(isinstance(node.init,DeclList)):  
            self.assert_declarations(node.init.decls)
        else: self.visit(node.init)

        if(node.cond):  self.visit(node.cond)
        if(node.next):  self.visit(node.next)
        if(node.stmt):  self.visit(node.stmt)
        
        self.scope_current=self.stk_sco.desempilha()
    def isWhat(self,value):
        try:
            aux=int(value)
        except:         
            if(len(value)==3):              return 'char'
            else:                           return 'string'
        if(aux==value):
            return 'int'
        else:
            return 'float'
    def visit_Print(self,node):
        if(node.expr):  self.visit(node.expr)
        
    def visit_ArrayRef(self,node):
        self.visit(node.name)
        self.visit(node.subscript)
        type1=node.name.type_name
        if(isinstance(node.subscript,ArrayRef)):    node.subscript.type_name=type1
        node.type_name=type1
        node.name_id=node.name        
        #Pode vir um cast,BinOp..
        if(isinstance(node.subscript,Constant) or isinstance(node.subscript,ID) ):
            if(isinstance(node.subscript,ID)):  type2=self.scope_current.table_type.lookup(node.subscript.name)
            else:                               type2=node.subscript.type
            assert 'int'==type2,f'// Error (canot assign index of array with {type2})'
        
    def visit_UnaryOp(self, node):
            self.visit(node.left)
            type=node.left.type_name
            node.type_name=type
            assert node.op in uc_types.get(type).unary_ops,f'// Error (unsupported op {node.op})'
    
    def visit_BinaryOp(self, node):
        # 1. Make sure left and right operands have the same type
        # 2. Make sure the operation is supported
        # 3. Assign the result type
        self.visit(node.left)
        self.visit(node.right)
        
       
        type1=node.left.type_name
        type2=node.right.type_name
        if node.op in binary_ops_visit:
            assert node.op in uc_types.get(type1).binary_ops,f'// Error (unsupported op {node.op})'
            assert node.op in uc_types.get(type2).binary_ops,f'// Error (unsupported op {node.op})'

            if(node.left.type_conc): node.left=node.left.type_conc
            if(node.right.type_conc): node.right=node.right.type_conc
            if((isinstance(node.left,Constant)) and (isinstance(node.right,Constant) )):
                type=None
                if(node.left.type_name=='float' or node.right.type_name=='float' ):
                    type = 'float'
                else:
                    type=type1
                    assert type1==type2, f'// Error. {type1}{node.op}{type2}'
                
                node.type_conc=Constant(value=node.left.value+node.right.value,type=type,coord=node.coord)
                node.type_name=type

            elif(isinstance(node.left,ID) and ((isinstance(node.right,Constant) ))):
                node.type_name=type1
                
                assert type2 in uc_types.get(type1).acept_literal, f'// Error. {type1}{node.op}{type2}'

            elif((isinstance(node.left,Constant) ) and isinstance(node.right,ID)):
                node.type_name=type2
                assert type1 in uc_types.get(type2).acept_literal, f'// Error. {type1}{node.op}{type2}'   
                        
            else: 

                node.type_name=type1
                assert type1==type2, f'// Error. {type1}{node.op}{type2}'
        else:
            node.type_name=type1
            if(type1):  assert node.op in uc_types.get(type1).rel_ops,f'// Error (unsupported op {node.op})'
            if(type2):  assert node.op in uc_types.get(type2).rel_ops,f'// Error (unsupported op {node.op})'
            assert type1==type2,f'// Error  Oparation  {node.op} between {type1} and {type2} line in line {node.left.coord.line} '
        if(node.op in rel_ops):
            node.type_name='bool'
        
             
    
    def visit_ID(self,node):
        type=self.scope_current.table_type.lookup(node.name)
        node.type_name=type
        assert type, f'// Error. {node.name} not defined on line {node.coord.line} column {node.coord.column}.'
    def visit_Constant(self,node):
        node.type_name=node.type
    def treat_array(self,type,array,init):
        if(init and init.exprs[0]):
            dim=len(init.exprs)
            if(array and array.dim):
                assert dim==array.dim.value,"// Error (size mismatch on initialization)"
            for ini in init.exprs:
                if(isinstance(ini,InitList)):
                    if(array):
                        self.treat_array(type,array.arraydecl,ini)
                    else:
                        self.treat_array(type,array,ini)
                else:
                    value=ini.value
                    what=self.isWhat(value)
                    assert what in uc_types.get(type).acept_literal  ,f'// Error (canot assign {what} to {type})'
        else:
            while(array and array.dim):
                assert array.dim.type=='int',f'// Error (canot assign index of array whith {array.dim.type})'
                array=array.arraydecl


