from blocks import *
from math import log , floor


class Optimization(object):
    def __init__(self,head=None,nos=[],code=[],begin=0,end=0,flag=True):
        self.nos=nos
        self.head=head
        self.code=code
        self.begin=begin
        self.end=end
        self.gdefs=dict()
        self.n=0
        self.n=begin-end+1
        self.expr_lin=dict()
        self.cop_take_4=set(['div',  'mod', 'mul' , 'sub', 'add'])
        self.cop_take_3=set(['load'])      
        self.assignment_4=set(['div',  'mod', 'mul' , 'sub', 'add', "elem","lt", "le", "ge", "gt", "eq", "ne", "and", "or", "not"])#Atribuições de tamanho 4
        self.assignment_3=set(['load' ,'literal','store' ,  'call','fptosi','sitofp',"get"]) #Atribuições de tamanho 3    
        self.ignore=set(['jump','define','alloc'])      
        self.flag=flag

    def optimization(self):
        self.reset()
        self.reaching_definitions()
        self.constant_propagation()
        self.liveness()
        self.dead_code()
        self.reset()    
            
    def reaching_definitions(self):
        #Pegamos todas as definições do bloco
        self.get_gdefinitions()
        for no in self.nos:
            gen,kill=0,0     
            for inst in no.instructions:
                aux=self.isAssignment(inst[0])
                if(len(inst)<2 or  self._ignore(inst[0]) or not aux):  continue
                _str=''
                for pt in inst:         _str+=f'{pt} '
                #no.gdefs[inst[-1]]=((no.gdefs.get(inst[-1]) or 0) | (self.expr_lin.get(_str[:-1]) | 0))#Todas definições do bloco
                gen_p=(self.expr_lin.get(_str[:-1]) | 0)#def pontual
                kill_p=((self.gdefs.get(inst[-1]) or 0) & ~gen_p)#kill pontual
                gen=(gen_p | (gen & ~kill))
                kill= (kill | kill_p)
            no.gen=gen
            no.kill=kill
            #print(no.label,bin(gen),bin(kill))
            
        change=True
        while(change):
            change=False
            for no in self.nos:
                if(no.label==self.head.label):  continue
                before=no.r_OUT
                for pred in no.predecessors:    no.r_IN=(no.r_IN | pred.r_OUT)       
                no.r_OUT=((no.gen) | (no.r_IN & ~no.kill))
                if(before!=no.r_OUT):           change=True

    def liveness(self):
        #Calcula use e defs de um bloco  
        for no in self.nos:
            tam=len(no.instructions)
            use,dfs=set(),set()
            for i in range(tam-1,-1,-1):
                use_p,dfs_p=set(),set()
                if(len(no.instructions[i])!=1 and  not self._ignore(no.instructions[i][0])):
                    aux=self.isAssignment(no.instructions[i][0])
                    if(aux==3):
                        if(type(no.instructions[i][-2])==str):  use_p.add(no.instructions[i][-2])
                        dfs_p.add(no.instructions[i][-1])
                    elif(aux==4):
                        dfs_p.add(no.instructions[i][-1])
                        use_p.add(no.instructions[i][-2])
                        use_p.add(no.instructions[i][-3])
                    else:
                        for pt in no.instructions[i][1:]:
                            if(type(pt)==str):  use_p.add(pt)
                use=(use-dfs_p) | use_p
                dfs=(dfs-use_p) | dfs_p
            no.use=use
            no.dfs=dfs
        #Gera os In e Outs
        change=True
        while(change):
            change=False
            for no in self.nos:
                before=no.l_IN
                sucs=[]
                #Take Out
                if(isinstance(no,ConditionBlock) and no.fall_through):  sucs.append(no.fall_through)
                if(no.next_block):                                      sucs.append(no.next_block)
                for suc in sucs:                                        no.l_OUT=no.l_OUT | suc.l_IN
                no.l_IN=no.use | (no.l_OUT-no.dfs)                        
                if(before!=no.l_IN):             change=True

    def dead_code(self):
        self.clear_jump()
        for no in self.nos:
            tam=len(no.instructions)
            use=no.l_OUT
            dfs=set()
            stores=dict()
            for i in range(tam-1,-1,-1):
                if(not no.instructions[i][0]): continue
                use_p,dfs_p=set(),set()
                st=True
                if(len(no.instructions[i])!=1 and  not self._ignore(no.instructions[i][0])):
                    aux=self.isAssignment(no.instructions[i][0])
                    if('store' in no.instructions[i][0]):
                         if(not stores.get(no.instructions[i][-1])):    
                            st=False
                            stores[no.instructions[i][-1]]=no.instructions[i][-2]
                    if(aux and no.instructions[i][-1] not in use and st):   
                        for k in range(len(no.instructions[i])):     no.instructions[i][k]=None
                        continue
                    #Continuo
                    if(aux==3):
                        if(type(no.instructions[i][-2])==str):  use_p.add(no.instructions[i][-2])
                        dfs_p.add(no.instructions[i][-1])
                    elif(aux==4):
                        dfs_p.add(no.instructions[i][-1])
                        use_p.add(no.instructions[i][-2])
                        use_p.add(no.instructions[i][-3])
                    else:
                        for pt in no.instructions[i][1:]:
                            if(type(pt)==str):  use_p.add(pt)
                use=(use-dfs_p) | use_p
                dfs=(dfs-use_p) | dfs_p

    def constant_propagation(self):
        
        for no in self.nos:
            reach=no.r_IN
            while(reach):            
                tam=floor(log(reach,2))
                reach=(reach & ~(1<<tam)) 
                if(not no.cop_var_var.get(self.code[tam][-1])):
                    if('literal' in self.code[tam][0]):     no.cop_var_var[self.code[tam][-1]]=self.code[tam][-2]
                    else:                                   no.cop_var_var[self.code[tam][-1]]='UNDEF'
                else:
                    no.cop_var_var[self.code[tam][-1]]='NAC'
            
            for inst in no.instructions:
                if('literal' in inst[0] or 'store' in inst[0]):       
                    no.cop_var_var[inst[-1]]=inst[-2]  
                    continue  

                aux=self.isCopyTake(inst[0])
                if(aux==4):
                    var1=no.cop_var_var.get(inst[-3])
                    var2=no.cop_var_var.get(inst[-2])
                    while(no.cop_var_var.get(var1) or no.cop_var_var.get(var1)==0):         var1=no.cop_var_var[var1]
                    while(no.cop_var_var.get(var2) or no.cop_var_var.get(var2)==0):         var2=no.cop_var_var[var2]
                    if(var1!=None and type(var1)!=str and var2!=None and type(var2)!=str):
                        if('add'  in inst[0]):                  inst[1]=var1+var2
                        elif('sub'  in inst[0]):                inst[1]=var1-var2
                        elif('mul' in inst[0]):                 inst[1]=var1*var2
                        elif('div' in inst[0]):
                            if(inst[0][-3:]=='int'):                 inst[1]=int(var1/var2)
                            else:                                    inst[1]=var1/var2
                        else:                                        inst[1]=var1%var2
                        tipo='float'
                        if(inst[0][-3:]=='int'):  tipo='int'
                        inst[0]=f'literal_{tipo}'
                        inst[2]=inst[3]
                        no.cop_var_var[inst[-1]]=inst[1]
                        del inst[3]       
                elif(aux==3):
                    var=inst[-2]
                    while(no.cop_var_var.get(var) or no.cop_var_var.get(var)==0 ):     var=no.cop_var_var[var]
                    tipo=type(var)
                    if(tipo!=str):
                        tipo='float'
                        if(inst[0][-3:]=='int'):  tipo='int'
                        
                        inst[0]=f'literal_{tipo}'
                        inst[1]=var
                    no.cop_var_var[inst[-1]]=var
                else:
                    pass
    def reset(self):
        for no in self.nos:
            no.visit=False
    def isCopyTake(self,expr):
        for op in self.cop_take_3:
            if(op in expr):
                return 3
        for op in self.cop_take_4:
            if(op in expr):
                return 4
        return False
        
    def get_gdefinitions(self):
        for i in range(self.begin,self.end):
            gen=1<<i
            if(len(self.code[i])>1 and not  self._ignore(self.code[i][0])): 
                aux=self.isAssignment(self.code[i][0])
                if(aux==3):

                    self.expr_lin[f'{self.code[i][0]} {self.code[i][1]} {self.code[i][2]}']=gen
                    self.gdefs[self.code[i][-1]]=(gen | (self.gdefs.get(self.code[i][-1]) or 0))
                elif(aux==4):
                    self.expr_lin[f'{self.code[i][0]} {self.code[i][1]} {self.code[i][2]} {self.code[i][3]}']=gen
                    self.gdefs[self.code[i][-1]]=(gen | (self.gdefs.get(self.code[i][-1]) or 0))
                else:
                    pass
            else:
                _str=''
                for pt in self.code[i]:
                    _str+=f'{pt} '
                    self.expr_lin[_str[:-1]]=gen

    def clear_jump(self):
        for no in self.nos:
            delete=False
            for inst in no.instructions:
                if(delete):
                    for k in range(len(inst)):           inst[k]=None
                if(type(inst[0])==str and 'jump' in inst[0] ):                   delete=True


    def _ignore(self,expr):
        for op in self.ignore:
            if(op in expr ):
                return True
        return False
        
    def isAssignment(self,expr):

        for op in self.assignment_3:
            if(  op in expr):
                return 3
        for op in self.assignment_4:
            if( op in expr):
                return 4
        return False
    def dfs(self,block):
        #Percorre o grafo em profundidade
        if( not isinstance(block, Block) or block.visit ):         return
        block.visit=True
        self.dfs(block.next_block)
        if(isinstance(block, ConditionBlock)):
            self.dfs(block.fall_through)
