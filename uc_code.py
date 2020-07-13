from ast import *
import copy
from blocks import *
from optimization import *
from llvm import *
######################## -> GenerateCode <- #######################
class CodeGenerator(NodeVisitor):
    '''
    Node visitor class that creates 3-address encoded instruction sequences.
    '''
    def __init__(self,cfg):
        self.queue_sco=Fila()
        self.stk_sco=Pilha()
        self.scope_current=None
        self.array_ref=Fila()
        self.binary_bool=rel_ops
        self.binary_ops=binary
        self.unary_ops=unary
        self.assign_op=assign_op
        self.array_name=Pilha()
        self.cfg=cfg
        self.code = []
        self.decl_glob = []
        self.heaps=dict()
        self.name_array='global'
        self.heaps[self.name_array]=0
        self.param_bool=True
        self.count=-1
        self.scopes=dict()
        self.code_opt=None


        self.cfgs=[]
        #\\\\\\\\Blocks/////////
        self.block_current=None
        self.stack_for=Pilha()
        self.blocks=[]
    def increase_count(self):
        self.count+=1
        return self.count
    def new_heap(self):
        '''
        Create a new heap  of a given array .
        '''
        if self.name_array not in self.heaps:
            self.heaps[self.name_array] = 0
        name = "@.str." + "%d" % (self.heaps[self.name_array])
        self.heaps[self.name_array] += 1
        return name
    
    
    def visit_Program(self,node):
        self.scopes['global']=Scope()
        for no in node.gdecls:
            self.scope_current=self.scopes.get('global')
            self.visit(no)
        code=copy.deepcopy(self.code)
        funcs=Fila()
        
        for _decl in node.gdecls:
            if isinstance(_decl, FuncDef):
                #Mostras cfgs não otimizados
                
                _decl.reset()         
                _decl.get_blocks_dfs(_decl.cfg)
                self.clear_jump(_decl.blocks)
                _decl.reset()         
                funcs.insere(_decl.blocks)
                #opt=Optimization(_decl.cfg,_decl.blocks,self.code,_decl.get_begin(),_decl.get_end())
                #opt.optimization()
                #_decl.reset()
                if(self.cfg):
                    dot = CFG(_decl.decl.id.name)
                    dot.view(_decl.cfg)
        self.clear_None()
        _llvm=LLVMFunctionVisitor(funcs,self.decl_glob,self.code)
        _llvm.gen_llvm()
                
        self.code_opt=self.decl_glob+self.code
        #self.code=self.decl_glob+code
        self.code=self.decl_glob+self.code
        


    def visit_GlobalDecl(self, node):
        self.assert_declarations_gloabals_before(node.gdecls or [])
        
    def visit_FuncDef(self,node):

        
        name=node.decl.id.name
        self.scope_current.table_type.add(f'@{name}',node.type)

        escopo=copy.deepcopy(self.scope_current)
        escopo.set_name(name)
        self.scope_current=escopo
        self.scopes[name]=escopo
        self.param_bool=True
        #escopo.new_temp()#Começamos no 1
        
        
        inst_def=[f'define_{node.type.names}','@'+name,[]]
        
        head_block=Block('define '+'@'+name)
        self.block_current=head_block
        
        
        
        self.block_current.append(self.increase_count(),inst_def)
        self.code.append(inst_def)
        self.block_current=head_block
        node.begin=self.count


        inst2=['%entry',]
        self.block_current.append(self.increase_count(),inst2)
        self.code.append(inst2)

        #\\\\\\\ Criamos um novo bloco para cada função////////#
        #self.code.append(inst2)
        node.cfg=self.block_current
        
        label="%exit"#label
        escopo.table_type.add(label,node.type)
        type_return=node.type.names          
        type=node.type.names
        if(node.type.names!="void"):
            target=escopo.new_temp()
            escopo.table.add(label,target)
            inst=[f'alloc_{type}',target]
            self.code.append(inst)
            self.block_current.append(self.increase_count(),inst)
            var_return=target
        params=[]
        if(node.decl.funcdecl.paramlist):      
            params=node.decl.funcdecl.paramlist.params
        #Percorremos paramlist para associar cada entrada a uma variável        
        for decl in params:
            t=escopo.new_temp()
            escopo.table.add(decl.id.name+'_in',t)
            escopo.table_type.add(decl.id.name+'_in',decl.vardecl.type)
            escopo.param_list.append([t,None ,decl.vardecl.type.names ])
            inst_def[2].append([decl.vardecl.type.names,t])
            

        #Variável que será o retorno da função
        #if(node.type.names!="void")
        label="%exit"#label
        escopo.table_type.add(label,node.type)
        type_return=node.type.names          
        #Término da função
        block_end=Block(label)
        self.stack_for.empilha(block_end)

        escopo.table.add('%saida',block_end)
        
        
        #Alocamos variáveis locais
        
        for i ,decl in enumerate(params):
            target=escopo.new_temp()
            escopo.table.add(decl.id.name,target)
            escopo.table_type.add(decl.id.name,decl.vardecl.type)
            type=decl.vardecl.type.names
            inst=[f'alloc_{type}',target]
            escopo.param_list[i][1]=target
            self.code.append(inst)
            self.block_current.append(self.increase_count(),inst)


              
        if(node.comp):
            self.visit(node.comp)
        

        target=self.scope_current.new_temp()
        if(type_return=='void'):
            inst1=['%exit', ]
            inst2=[f'return_{type_return}']
            block_end.append(self.increase_count(),inst1)
            block_end.append(self.increase_count(),inst2)
            self.code.append(inst1)
            self.code.append(inst2)
        else:

            inst1=['%exit' ]
            inst2=[f'load_{type_return}',var_return,target]
            inst3=[f'return_{type_return}',target]

            block_end.append(self.increase_count(),inst1)
            block_end.append(self.increase_count(),inst2)
            block_end.append(self.increase_count(),inst3)
            self.code.append(inst1)
            self.code.append(inst2)
            self.code.append(inst3)
        
        node.end=self.count
        self.block_current.next_block=block_end
        block_end.predecessors.append(self.block_current)
        '''
        label2=self.scope_current.new_temp()
        #self.increase_count
        for i in range(node.begin,node.end):
            if(len(self.code[i])>0):
                op=self.code[i][0]
                if('jump' in op and 'exit' in self.code[i][1]):     self.code[i][1]=label2
                elif('exit' in op):                                 self.code[i][0]=label2[1:]
                #elif('entry' in op):                                self.code[i][0]=label1[1:]
        '''
        self.block_current=block_end
        self.param_bool=False
            
             
    def visit_Compound(self,node):
        #A função abaixo trata todas as possíveis declarações de uma função e faz as devidas alocações

        
        
        self.alloc_declarations_list(node.decl)
        self.alloc_declarations_sts(node.st)
        #Store os parametros
        if(self.param_bool):
            self.param_bool=False
            for param in self.scope_current.param_list:
                inst=[f'store_{param[2]}', param[0], param[1]]
                self.code.append(inst)
                self.block_current.append(self.increase_count(),inst)
            
        self.store_declarations_list(node.decl)
        self.store_declarations_sts(node.st)

        if(node.st[0]):
            for no in node.st:
                self.visit(no)
    #Andamento
        
    
    def visit_While(self, node):
        self.stk_sco.empilha(self.scope_current)
        escopo=copy.deepcopy(self.scope_current)#Cria um novo escopo cópia, assim ele pode enxergar fora e dentro
        self.scope_current=escopo
       
        #Se for uma bloco com apenas uma label, fazemos ele ser a label atual
        flag=True
        if(len(self.block_current.instructions)==1 and len(self.block_current.instructions[0])==1):
            self.block_current.changeClass(self.block_current,ConditionBlock)
            block=self.block_current
            label1="%"+self.block_current.instructions[0][0]
            flag=False
        else:
            label1=escopo.new_temp()
            inst=["jump",label1]
            self.code.append(inst)
            self.block_current.append(self.increase_count(),inst)
            block=ConditionBlock(label1)

        #Labels para o Branch
        label2=escopo.new_temp()
        label3=escopo.new_temp()
        

        #\\\\\\\Criamos os 3 blocos do FOR: cond, True e False
        block1=block
        blockT=Block(label2)
        blockF=Block(label3)
       

        self.stack_for.empilha(blockF)

        self.block_current.next_block=block1
        block1.predecessors.append(self.block_current)

        block1.next_block=blockT
        block1.fall_through =blockF
        blockT.predecessors.append(block1)
        blockF.predecessors.append(block1)
        
        blockT.next_block=block1
        block1.predecessors.append(blockT)

        self.block_current=block1

        #Construímos bloco 1
        if(flag):       
            inst1=[label1[1:],]
            self.code.append(inst1)
            self.block_current.append(self.increase_count(),inst1)
        if(node.cond):     
            self.visit(node.cond)
            inst=['cbranch', node.cond.gen_location, label2, label3]
            self.code.append(inst)
            self.block_current.append(self.increase_count(),inst)
        #Fim



       
        #Construimos o block body do for
        self.block_current=blockT
        inst2=[label2[1:],]
        self.code.append(inst2)
        self.block_current.append(self.increase_count(),inst2)
        if(node.stmt):     self.visit(node.stmt)
        if(not ("jump" in  self.block_current.instructions[-1][0])):
            inst3=['jump',label1]
            self.code.append(inst3)
            self.block_current.append(self.increase_count(),inst3)
        #Fim




        self.block_current.next_block=block1
        self.block_current=blockF        
        
        inst4=[label3[1:],]
        self.code.append(inst4)
        self.block_current.append(self.increase_count(),inst4)
        #Fim
    
        self.stack_for.desempilha()

        escopo=self.scope_current
        self.scope_current=self.stk_sco.desempilha()
        self.scope_current.vars[escopo.name]=escopo.vars[escopo.name]

    def visit_For(self,node):
         #Em anandamento
        self.stk_sco.empilha(self.scope_current)
        escopo=copy.deepcopy(self.scope_current)#Cria um novo escopo cópia, assim ele pode enxergar fora e dentro
        self.scope_current=escopo
        
        
        if(isinstance(node.init,DeclList)):     pass
        else:                                   self.visit(node.init)

        label0=escopo.new_temp()
       
        #Se for uma bloco com apenas uma label, fazemos ele ser a label atual
        #flag=True
        '''      if(len(self.block_current.instructions)==1 and len(self.block_current.instructions[0])==1):
                    self.block_current.changeClass(self.block_current,ConditionBlock)
                    block=self.block_current
                    label1="%"+self.block_current.instructions[0][0]
                    flag=False
                else:
        '''          
        label1=escopo.new_temp()
        #Labels para o Branch
        label2=escopo.new_temp()
        label3=escopo.new_temp()
        

        #\\\\\\\Criamos os 3 blocos do FOR: cond, True e False
        block1=ConditionBlock(label1)
        blockT=Block(label2)
        blockF=Block(label3)
        block_incr=Block(label0)

        self.stack_for.empilha(blockF)

        
        self.block_current.next_block=block1
        block1.predecessors.append(self.block_current)

        block1.next_block=blockT
        block1.fall_through =blockF
        blockT.predecessors.append(block1)
        blockF.predecessors.append(block1)
        
        block_incr.next_block=block1
        block1.predecessors.append(block_incr)
        inst=["jump",block1.label]
        self.code.append(inst)
        self.block_current.append(self.increase_count(),inst)

        self.block_current=block1

        #Construímos bloco 1
        inst1=[label1[1:],]
        self.code.append(inst1)
        self.block_current.append(self.increase_count(),inst1)
        if(node.cond):     
            self.visit(node.cond)
            #if(node.next):     self.visit(node.next)# Não é preciso criar um bloco apenas para o next.

            inst=['cbranch', node.cond.gen_location, label2, label3]
            self.code.append(inst)
            self.block_current.append(self.increase_count(),inst)
        #Fim

       
        #Construimos o block body do for
        self.block_current=blockT
        inst2=[label2[1:],]
        self.code.append(inst2)
        self.block_current.append(self.increase_count(),inst2)
        if(node.stmt):     self.visit(node.stmt)
        #print(self.block_current.instructions[-1][0])
        '''if(not ("jump" in  self.block_current.instructions[-1][0])):
            inst3=['jump',label0]
            self.code.append(inst3)
            self.block_current.append(self.increase_count(),inst3)
        '''#Fim
        if(self.block_current.label!=blockT.label):
            label=block_incr.label
            inst_jump=["jump",label]
            self.code.append(inst_jump)
            self.block_current.append(self.increase_count(),inst_jump)
        

        #Next
        self.block_current.next_block=block_incr
        self.block_current=block_incr
        inst_inc=[block_incr.label[1:],]
        self.block_current.append(self.increase_count(),inst_inc)
        self.code.append(inst_inc)
        self.visit(node.next)
        inst5=['jump',block1.label]
        self.block_current.append(self.increase_count(),inst5)
        self.code.append(inst5)
        
        #fim
        
        
        #Construimos o block de saída do  for
        self.block_current=blockF
        self.block_current=blockF
        inst4=[label3[1:],]
        self.code.append(inst4)
        self.block_current.append(self.increase_count(),inst4)
        #Fim
    
        self.stack_for.desempilha()

        escopo=self.scope_current
        self.scope_current=self.stk_sco.desempilha()
        self.scope_current.vars[escopo.name]=escopo.vars[escopo.name]
    
        
        
    def visit_FuncCall(self,node):
        name=node.name.name
        aux=[]
        if node.args:
            for param in (node.args.exprs):
                self.visit(param)
                #E se for um vetor, função etc?
                type=param.type_name
                '''if(isinstance(param,ID)): type=self.scope_current.table_type.lookup(param.name).names
                else:                     type=type. 
                '''
                inst=[f'param_{type}',param.gen_location]
                aux.append(inst)
                #self.code.append(inst1)    
                    
            for i in range(len(aux)):
                self.code.append(aux[i])
                self.block_current.append(self.increase_count(),aux[i])
   
        target=self.scope_current.new_temp()
        inst=[f'call',f'@{name}',target]
        node.gen_location=target
        node.type_name=self.scope_current.table_type.lookup(f'@{name}').names
        self.code.append(inst)
        self.block_current.append(self.increase_count(),inst)

        #?
                    
    ################################Arrumados
    def visit_If(self,node):
        
        #Transformamos o bloco atual em um condicional bloco
        self.block_current.changeClass(self.block_current,ConditionBlock)
        label1 = self.scope_current.new_temp()
        label2 = self.scope_current.new_temp()
        #block_then = BasicBlock(label1)
        block_then=Block(label1)
        block_else=Block(label2)
        self.block_current.next_block=block_then
        self.block_current.fall_through=block_else
        block_then.predecessors.append(self.block_current)
        block_else.predecessors.append(self.block_current)
        
        
        

        if(node.iftrue and node.iffalse):
            label3 = self.scope_current.new_temp()
            block_out=Block(label3)
            block_then.next_block=block_out
            block_else.next_block=block_out
            
            #Condição
            self.visit(node.cond)
            inst1=['cbranch',node.cond.gen_location,label1 , label2]
            self.code.append(inst1)
            self.block_current.append(self.increase_count(),inst1)
            
            #BlocoThen
            self.block_current=block_then
            inst2=[label1[1:],]
            self.code.append(inst2) 
            self.block_current.append(self.increase_count(),inst2)
            self.visit(node.iftrue)
            #Aceitamos que o bloco que o  break chama ganhe jump duplo
            inst3=['jump', label3]
            self.code.append(inst3)
            self.block_current.append(self.increase_count(),inst3)
            block_out.predecessors.append(self.block_current)
            #Fim

            #BlocoElse
            self.block_current=block_else
            inst4=[ label2[1:] , ]
            self.code.append(inst4)
            self.block_current.append(self.increase_count(),inst4)
            self.visit(node.iffalse)
            #Aceitamos que o bloco que o  break chama ganhe jump duplo
            inst3=['jump', label3]
            self.code.append(inst3)
            self.block_current.append(self.increase_count(),inst3)
            block_out.predecessors.append(self.block_current)
            #Fim
            
            #BlocoOut
            ''' 
                flag_out=False
                if(block_then.next_block.label==block_out.label):
                    block_out.predecessors.append(block_then)
                    flag_out=True
                if (block_else.next_block.label==block_out.label):
                    block_out.predecessors.append(block_else)
                    flag_out=True

                if(flag_out):
            '''    

            self.block_current=block_out
            inst5=[ label3[1:] , ]
            self.code.append(inst5)   
            self.block_current.append(self.increase_count(),inst5)
            
            self.block_current=block_out

        else:

            block_then.next_block=block_else
            block_else.predecessors.append(block_then)
           
            self.visit(node.cond)
            inst1=['cbranch',node.cond.gen_location,label1 , label2]
            self.code.append(inst1)
            self.block_current.append(self.increase_count(),inst1)


            #BlocoThen
            self.block_current=block_then            
            inst2=[label1[1:],]
            
            self.code.append(inst2)
            self.block_current.append(self.increase_count(),inst2)            
            self.visit(node.iftrue)
            if(not "jump" in self.block_current.instructions[-1][0]): 
                inst3=['jump', label2]
                self.code.append(inst3)
                self.block_current.append(self.increase_count(),inst3)            
                
            

            #Bloco out = else nesse caso 
            self.block_current=block_else
            inst3=[label2[1:],]
            self.code.append(inst3)
            self.block_current.append(self.increase_count(),inst3)

    def visit_Break(self,node):
        self.stack_for.empilha(self.block_current)
        for block in self.stack_for.dados:
            print("oi",block.label)
        block=self.stack_for.penultimo()
        print(block.label)
        #print(block.label)
        inst=['jump',block.label]
        self.code.append(inst)
        self.block_current.append(self.increase_count(),inst)
        self.block_current.next_block=block
    
        
    def visit_Assert(self, node):
        self.visit(node.expr)
        self.block_current.changeClass(self.block_current,ConditionBlock)
        #self.code
        label1=self.scope_current.new_temp()
        label2=self.scope_current.new_temp()
        
        
        block_True=Block(label1)
        block_False=Block(label2)        
        block_exit=self.scope_current.table.lookup("%saida")

        #Precedências e Sucessores
        self.block_current.next_block=block_True
        self.block_current.fall_through=block_False
        block_True.predecessors.append(self.block_current)
        block_False.predecessors.append(self.block_current)
        block_False.next_block=block_exit
        block_exit.predecessors.append(block_False)
        
        
        inst0=['cbranch',node.expr.gen_location,label1,label2]
        self.block_current.append(self.increase_count(),inst0)
        self.code.append(inst0)

        

        #Bloco False
        inst3=[label2[1:],]
        target=self.new_heap()
        inst_3_4=['global_string',target,f'assertion_fail on  {node.coord.line}:{node.coord.column}']
        inst4=['print_string', target]
        inst5=['jump',"%exit"]#pra um lugar certo
        block_False.append(self.increase_count(),inst3)
        block_False.append(self.increase_count(),inst4)
        block_False.append(self.increase_count(),inst5)
        self.code.append(inst3)
        self.code.append(inst4)
        self.code.append(inst5)
        self.decl_glob.append(inst_3_4)



        #Bloco True
        inst1=[label1[1:],]
        block_True.append(self.increase_count(),inst1)
        self.code.append(inst1)



        #label3, Continuação do True
        self.block_current=block_True

         
        
        
    def visit_Return(self, node):
        escopo=self.scope_current
        label="%exit"
        block_exit=self.scope_current.table.lookup("%saida")
        self.block_current.next_block=block_exit
        block_exit.predecessors.append(self.block_current)

        if (node.expr):
             self.visit(node.expr)
             var_return=escopo.table.lookup(label)
             type=escopo.table_type.lookup(label).names
             result=node.expr.gen_location
             inst1=[f'store_{type}',result ,var_return ]
             inst2=['jump',label]
             self.code.append(inst1)
             self.code.append(inst2)
             self.block_current.append(self.increase_count(),inst1)   
             self.block_current.append(self.increase_count(),inst2)
        else:    
            inst=['jump',label]
            self.code.append(inst)
            self.block_current.append(self.increase_count(),inst)

  
        
    def visit_Read(self,node):
        if(node.expr and isinstance(node.expr[0],list)):
            for no in node.expr:
                self.visit(no)
                inst=[f'read_{no.type_name}',no.gen_location]
                self.code.append(inst)
                self.block_current.append(self.increase_count(),inst)
        
        elif(node.expr and isinstance(node.expr[0],ExprList)):
            for no in (node.expr[0].exprs or []):
                self.visit(no)
                inst=(f'read_{no.type_name}',no.gen_location)
                self.code.append(inst)
                self.block_current.append(self.increase_count(),inst)
        elif(node.expr):
            no=node.expr[0]
            self.visit(no)
            inst=[f'read_{no.type_name}',no.gen_location]
            self.code.append(inst)
            self.block_current.append(self.increase_count(),inst)

        else:
            inst=['read_void',]
            self.code.append(inst)
            self.block_current.append(self.increase_count(),inst)

    def visit_ExprList(self,node):
        for no in node.exprs:
            self.visit(no)
    
    
    
        
    def visit_Print(self,node):

        if(node.expr):
            if(isinstance(node.expr,ExprList)):
                for e in node.expr.exprs:
                    if(isinstance(e,Constant) and e.type=='string'):
                        target=self.new_heap()
                        inst1=[f'global_{e.type}_{len(e.value)}',target,e.value[1:-1]]
                        inst2=['print_string', target]
                        self.code.append(inst2)
                        self.block_current.append(self.increase_count(),inst2)
                        self.decl_glob.append(inst1)
                    
                    else:
                        inst2=None
                        self.visit(e)
                        tgt=self.scope_current.new_temp()  
                        inst1=[f'load_{e.type_name}',e.gen_location,tgt]
                        if(e.type_name[-1]=='*'):   inst2=[f'print_{e.type_name[:-2]}',tgt ]
                        else:                       inst2=[f'print_{e.type_name}',tgt ]
                        self.code.append(inst1)
                        self.code.append(inst2)
                        self.block_current.append(self.increase_count(),inst1)
                        self.block_current.append(self.increase_count(),inst2)
            else:
                inst2=None
                self.visit(node.expr)
                #tgt=self.scope_current.new_temp()  
                tgt=node.expr.gen_location
                #inst1=[f'load_{node.expr.type_name}',node.expr.gen_location,tgt]
                if(node.expr.type_name[-1]=='*'):   inst2=[f'print_{node.expr.type_name[:-2]}',tgt ]
                else:                       inst2=[f'print_{node.expr.type_name}',tgt ]
                #self.code.append(inst1)
                self.code.append(inst2)
                #self.block_current.append(self.increase_count(),inst1)
                self.block_current.append(self.increase_count(),inst2)

        else:
            inst=['print_void', ]
            self.code.append(inst)
            self.block_current.append(self.increase_count(),inst)


             

    def visit_Assignment(self,node):
        escopo=self.scope_current
        flag=False
        
        if(node.op!='='):   flag=True
        if(isinstance(node.lvalue,ArrayRef)):

            self.visit(node.rvalue)
            self.visit(node.lvalue)
            name=node.lvalue.gen_name
            type1=node.rvalue.type_name
            type2=node.lvalue.type_name
            tgt=self.scope_current.new_temp()
            inst1=[f'load_{type1}', node.rvalue.gen_location,tgt]
            inst2=[f'store_{type2}', tgt, node.lvalue.gen_location]
            self.code.append(inst1)
            self.code.append(inst2)
            self.block_current.append(self.increase_count(),inst1)
            self.block_current.append(self.increase_count(),inst2)

        
        
        else:
            type=escopo.table_type.lookup(node.lvalue.name).names
                           
            if(isinstance(node.rvalue,UnaryOp)):
                #Aquii
                var=escopo.table.lookup(node.lvalue.name)
                if(node.rvalue.op=='&'):
                    self.visit(node.rvalue)
                    inst=[f'{self.unary_ops.get(node.rvalue.op)}_{type}',node.rvalue.gen_location,var]
                    node.gen_location=var
                    self.code.append(inst)
                    self.block_current.append(self.increase_count(),inst)
                elif(node.rvalue.op=='++'):
                
                    self.visit(node.rvalue)
                    inst=[f'store_{type}',node.rvalue.gen_location,var]
                    node.gen_location=var
                    self.code.append(inst)
                    self.block_current.append(self.increase_count(),inst)
                elif(node.rvalue.op=='p++'):
                    
                    self.visit(node.rvalue.left)
                    inst=[f'store_{type}',node.rvalue.left.gen_location,var]
                    node.gen_location=var
                    self.code.append(inst)
                    self.block_current.append(self.increase_count(),inst)         
                    self.visit(node.rvalue) 
                else:
                    self.visit(node.rvalue)

            elif(isinstance(node.rvalue,ArrayRef)):
                self.visit(node.rvalue)
                target=escopo.new_temp()
                type1=escopo.table_type.lookup(node.rvalue.gen_name).names
                inst1=[f'load_{type1}',node.rvalue.gen_location,target]

                var=escopo.table.lookup(node.lvalue.name)
                type2=escopo.table_type.lookup(node.lvalue.name).names                
                inst2=[f'store_{type2}',target,var]
                
                self.code.append(inst1)
                self.code.append(inst2)
                self.block_current.append(self.increase_count(),inst1)
                self.block_current.append(self.increase_count(),inst2)
        
            else:
                #Cast,Constant, BinaryOp,ID
                if(flag): 
                    bin=BinaryOp(op=self.assign_op.get(node.op),left=node.lvalue,right=node.rvalue)
                    self.visit(bin)
                    inst=[f'store_{type}', bin.gen_location, escopo.table.lookup(node.lvalue.name)]
                    node.gen_location=escopo.table.lookup(node.lvalue.name)


                else:
                    self.visit(node.rvalue)
                    inst=[f'store_{type}', node.rvalue.gen_location, escopo.table.lookup(node.lvalue.name)]
                    node.gen_location=escopo.table.lookup(node.lvalue.name)
                
                self.code.append(inst)
                self.block_current.append(self.increase_count(),inst)

    def visit_ArrayRef(self,node):
        escopo=self.scope_current
        self.visit(node.name)
        self.visit(node.subscript)
        if(node.subscript.type_name=='float' or node.name.type_name=='float'):  node.type_name='float'
        elif(node.subscript.type_name=='int' or node.name.type_name=='int'):    node.type_name='int'
        else:                                                                   node.type_name='char'
        type=node.type_name
        node.gen_name=node.name.gen_name
        inst1,inst2,inst3,inst4,inst5=None,None,None,None,None
        node.type_name=type
        if(isinstance(node.name,ID)):
            dim=self.scope_current.table.lookup(self.scope_current.table.lookup(node.name.name))
            literal=1
            if(dim):    
                for i in dim[1:]:   self.array_ref.insere(i)
                literal=dim[0]
            tgt1=escopo.new_temp()
            tgt3=escopo.new_temp()
            tgt4=escopo.new_temp()
            var1=node.subscript.gen_location
            var2=node.name.gen_location
            inst1=[f'literal_int',literal, tgt1]
            inst3=[f'mul_int',tgt1, var1, tgt3]
            node.gen_location=tgt3
            self.array_name.empilha(node.name.gen_location)
            self.array_name.empilha(node.name.name)
            if(self.array_ref.vazia()): 

                type=self.scope_current.table_type.lookup(self.array_name.desempilha()).names.split('_')[0]
                inst4=[f'elem_{type}',self.array_name.desempilha(),tgt3,tgt4]
                node.type_name=f'{type}_*'
                node.gen_location=tgt4
            node.gen_name=node.name.name
        else:
            literal=self.array_ref.retira()
            tgt1=escopo.new_temp()
            tgt3=escopo.new_temp()
            tgt4=escopo.new_temp()
            var1=node.subscript.gen_location
            var2=node.name.gen_location
            inst1=[f'literal_int',literal, tgt1]
            inst3=[f'mul_int',tgt1, var1, tgt3]                           
            inst4=[f'add_int',var2,tgt3,tgt4]
            node.gen_location=tgt4

            if(self.array_ref.vazia()): 
                tgt5=escopo.new_temp()
                type=self.scope_current.table_type.lookup(self.array_name.desempilha()).names.split('_')[0]

                inst5=[f'elem_{type}', self.array_name.desempilha(),tgt4,tgt5]
                node.type_name=f'{type}_*'
                node.gen_location=tgt5


        if(inst1):   self.code.append(inst1),self.block_current.append(self.increase_count(),inst1)
        if(inst2):   self.code.append(inst2),self.block_current.append(self.increase_count(),inst2)
        if(inst3):   self.code.append(inst3),self.block_current.append(self.increase_count(),inst3)
        if(inst4):   self.code.append(inst4),self.block_current.append(self.increase_count(),inst4)
        if(inst5):   self.code.append(inst5),self.block_current.append(self.increase_count(),inst5)

    def visit_Cast(self, node):
        escopo=self.scope_current
        self.visit(node.expr)
        target = escopo.new_temp()

        if(node.to_type.names=="int"):
            inst=['fptosi', node.expr.gen_location,target ]
            node.type_name='int'
        else:
            inst=['sitofp', node.expr.gen_location,target ]
            node.type_name='float'
        node.gen_location=target

        self.code.append(inst)
        self.block_current.append(self.increase_count(),inst)

         

        
    def visit_BinaryOp(self, node):
        # Visit the left and right expressions
        escopo=self.scope_current
        self.visit(node.left)
        self.visit(node.right)
        if(node.left.type_name=='float' or node.left.type_name=='float'): node.type_name='float'
        elif(node.left.type_name=='int' or node.left.type_name=='int'):   node.type_name='int'
        elif(node.left.type_name=='bool' or node.left.type_name=='bool'): node.type_name='bool'    
        else:                                                             node.type_name='char'
        type=node.type_name
        target = escopo.new_temp()
        # Create the opcode and append to list
        opcode = self.binary_ops[node.op] + "_"+type
        
        inst = [opcode, node.left.gen_location, node.right.gen_location, target]
        if(node.op in self.binary_bool  ):                node.type_name='bool'


        node.gen_location = target
        self.code.append(inst)
        self.block_current.append(self.increase_count(),inst)
        
   
    def visit_ID(self,node):
        #Preciso vincular cada vsriaavel com um tipo
        escopo=self.scope_current
        node.type=escopo.table_type.lookup(node.name)  
        if(isinstance(node.type,Type)):    node.type_name=node.type.names
        else:                                   node.type_name=node.type
        target=escopo.new_temp()
        node.gen_name=node.name
        inst=[f'load_{node.type_name}',escopo.table.lookup(node.name) , target]


        node.gen_location=target
        self.code.append(inst)
        self.block_current.append(self.increase_count(),inst)



    
    def visit_Constant(self,node):
        escopo=self.scope_current
        target=escopo.new_temp()
        inst=[f'literal_{node.type}',node.value ,target ]
        node.type_name=node.type
        node.gen_location=target
       
        self.code.append(inst)
        self.block_current.append(self.increase_count(),inst)

        
    def visit_UnaryOp(self, node):
        escopo=self.scope_current
        if node.right: self.visit(node.right)
        
        inst1,inst2=None,None
        target=None
        name=node.left.name

        type=escopo.table_type.lookup(name)
        if(type):   type=type.names
        else:       type=node.left.type_name
        
        if(not (node.op=='&') ):
            self.visit(node.left)    
            target = escopo.new_temp()

            inst1 = [f'{self.unary_ops[node.op]}_{type}', node.left.gen_location,node.right.gen_location,target]
            inst2 = [f'store_{type}', target,escopo.table.lookup(name)]
            node.gen_location=target
        
        elif(node.op=='&'):
            self.visit(node.left)
            node.gen_location=node.left.gen_location
    
        if inst1: 
            self.code.append(inst1)
            self.block_current.append(self.increase_count(),inst1)
        if inst2:
            self.code.append(inst2)
            self.block_current.append(self.increase_count(),inst2)



    def get_literal(self,node):
            self.scope_current.name_array=self.scope_current.name
            if(node.arraydecl and node.const):
                #char a="string";

                return (self.new_heap(), node.const.value)        
            elif(node.const):
                #int x=1;
                return (node.const.value,None)
            elif(node.arraydecl and node.initlist):
                return []
                #x[]={{1,2},{1,2}...}
            elif(node.arraydecl and node.arraydecl.dim):
                nada=True
            elif(node.ptrs):
                return []
            else:
                return []
    def alloc_declarations_list(self,decls):
        escopo=self.scope_current
        if(decls[0]):
            for nod in decls:
                for  no in nod:
                    aux1=escopo.new_temp()
                    name=no.id.name
                    escopo.table.add(no.id.name,aux1)
                    escopo.table_type.add(no.id.name,no.vardecl.type)  
                    inst=None
                    dim=None
                    if(no.arraydecl and no.const):
                        #char a="string";
                        no.vardecl.type.names='char'
                        escopo.table_type.add(no.id.name,no.vardecl.type)  
                        no.vardecl.type.names+=f'_{len(no.const.value)-2}'
                        
                        inst=[f'alloc_{no.vardecl.type.names}', aux1]
                        dim=[len(no.const.value)-2]
                        escopo.table.add(aux1,dim)
  
                    elif(no.const):
                        #int x=1;
                        
                        inst=[f'alloc_{no.vardecl.type.names}', aux1]
                    elif(no.arraydecl and no.initlist):
                        #x[]={{1,2},{1,2}...}
                        init=no.initlist
                        string=f'alloc_{no.vardecl.type.names}_{len(init.exprs)}'
                        dim=[len(init.exprs)]
                        no.vardecl.type.names+=f'_{len(init.exprs)}'
                        
                        init=init.exprs[0]
                        while( isinstance(init,InitList) and len(init.exprs)>1):
                            string=string+f'_{len(init.exprs)}'
                            no.vardecl.type.names+=f'_{len(init.exprs)}'
                            dim.append(len(init.exprs))
                            init=init.exprs[0]
                        escopo.table.add(aux1,dim)
                        inst=[string,aux1]
                    elif(no.arraydecl and no.arraydecl.dim):
                        #int x[2];
                        arr=f'alloc_{no.vardecl.type.names}_{no.arraydecl.dim.value}'
                        dim=[no.arraydecl.dim.value]
                        no.vardecl.type.names+=f'_{no.arraydecl.dim.value}'

                        tmp=no.arraydecl.arraydecl
                        while(tmp):
                            if(isinstance(tmp.dim,Constant)):     
                                arr+=f'_{tmp.dim.value}'
                                no.vardecl.type.names+=f'_{tmp.dim.value}'
                                dim.append(tmp.dim.value)
                            tmp=tmp.arraydecl
                        escopo.table.add(aux1,dim)
                        inst=[arr, aux1]
                    elif(no.funccall):
                        inst=[f'alloc_{no.vardecl.type.names}', aux1]
                    elif(no.ptrs):
                        part=f'alloc_{no.vardecl.type.names}'
                        inst=[part, aux1]
                    elif(no.id_2):
                        inst=[f'alloc_{no.vardecl.type.names}', aux1]
                    elif(no.binop):
                        inst=[f'alloc_{no.vardecl.type.names}', aux1]

                    else:
                        #int x[];
                        inst=[f'alloc_{no.vardecl.type.names}', aux1]
                        
                    if(inst):   
                        self.code.append(inst)
                        self.block_current.append(self.increase_count(),inst)
                    if(dim):
                        self.lineariza(dim)
                        

    def lineariza(self,dim):
        cop=dim.copy()
        for i in range(len(dim)):
            aux=1
            for j in range(i+1,len(dim)):
                aux=aux*cop[j]
            dim[i]=aux


    def store_declarations_list(self,decls):
        #Store literais
        escopo=self.scope_current
        if(decls[0]):
            for nod in decls: 
                for  no in nod:
                    aux1=escopo.table.lookup(no.id.name)
                    type=escopo.table_type.lookup(no.id.name)
                    if(no.arraydecl and no.const):
    
                        #Caso em que char ou string    
                        target=self.new_heap()
                        inst1=[f'store_{no.vardecl.type.names}',target,aux1 ]
                        inst2=[f'global_{no.vardecl.type.names}',target,list(no.const.value[1:-1])]
                        self.code.append(inst1)  
                        self.block_current.append(self.increase_count(),inst1)               

                        self.decl_glob.append(inst2)

                    elif(no.const ): 
                        #Caso do tipo x=const;
                        aux2=escopo.new_temp()
                        inst1=[f'literal_{no.vardecl.type.names}', no.const.value, aux2]
                        inst2=[f'store_{no.vardecl.type.names}', aux2, aux1]
                        self.code.append(inst1)
                        self.code.append(inst2)
                        self.block_current.append(self.increase_count(),inst1)               
                        self.block_current.append(self.increase_count(),inst2)               
                        
                    elif(no.arraydecl and no.initlist):
                        #caso do tipo x[]={const,const,const} or x[][]=...
                        str_local=f'store_{no.vardecl.type.names}'
                        str_global=f'global_{no.vardecl.type.names}'
                        values=[]
                        self.get_Decl(no.initlist,values)
                        target=self.new_heap()
                        inst1=[str_local,target, aux1]
                        inst2=[str_global,target, values]
                        
                        self.code.append(inst1) 
                        self.block_current.append(self.increase_count(),inst1)

                        self.decl_glob.append(inst2)  


                    elif(no.funccall):
                        self.visit(no.funccall)
                        inst=[f'store_{type.names}',no.funccall.gen_location, aux1]
                        self.code.append(inst)
                        self.block_current.append(self.increase_count(),inst)


                    elif(no.id_2):
                        target=self.scope_current.new_temp()
                        aux2=escopo.table.lookup(no.id_2.name)
                        inst1=[f'load_{no.vardecl.type.names}', aux2, target]
                        inst2=[f'store_{no.vardecl.type.names}', target, aux1]
                        self.code.append(inst1)
                        self.code.append(inst2)
                        self.block_current.append(self.increase_count(),inst1)
                        self.block_current.append(self.increase_count(),inst2)
                    elif(no.binop):
                        self.visit(no.binop)
                        inst=[f'store_{type.names}',no.binop.gen_location, aux1]
                        self.code.append(inst)
                        self.block_current.append(self.increase_count(),inst)
                    else:
                        pass

    def get_Decl(self,pai,defs=[]):
        if(not pai):    return defs
        for filho in pai.exprs:
            if(isinstance(filho,InitList)):         defs=self.get_Decl(filho,defs)
            else:
                if(isinstance(filho,Constant)):     defs.append(filho.value)
        return defs

                        
    def alloc_declarations_sts(self,sts):     
        if(sts[0]):
            for no in sts:
                if(isinstance(no,For)):
                    if(isinstance(no.init,DeclList)):
                        self.alloc_declarations_list([no.init.decls])

    
    def store_declarations_sts(self,sts):     
        if(sts[0]):
            for no in sts:
                if(isinstance(no,For)):
                    if(isinstance(no.init,DeclList)):
                        self.store_declarations_list([no.init.decls])
    


    def assert_declarations_gloabals_before(self,node):
        "Trada declarações globais antes dos escopos das funções"
        for decl in node:
            name_id=decl.id.name
            type=decl.vardecl.type
            self.scope_current.table.add(name_id,f'@{name_id}')
            self.scope_current.table_type.add(name_id,type)
            literal=self.get_literal(decl)
            if(literal):
                if literal[1]: inst=[f'global_{type.names}',f'@{name_id}',literal[0],literal[1]]
                else:          inst=[f'global_{type.names}',f'@{name_id}',literal[0]]
            else:
                inst=[f'global_{type.names}',f'@{name_id}']
            self.decl_glob.append(inst)
    
    def clear_None(self):
        code=[]
        for inst in self.code:
            if(inst[0]):    code.append(inst)
        self.code=code
    def clear_jump(self,blocks):
        for b in blocks:
            flag=False
            insts=[]
            for inst in b.instructions:
                if( not flag):               insts.append(inst)
                else:                        inst[0]=None
                if('jump'==inst[0]):       
                    flag=True
            b.instructions=insts

