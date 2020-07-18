from llvmlite import ir, binding
from ctypes import CFUNCTYPE, c_int
from engine_llvm import Engine_LLVM
class LLVMCodeGenerator():
    def __init__(self,blocks,var_globals,code_funcs,cfg):
        self.cfg=cfg#Ver depois
        self.engine=Engine_LLVM()
        self.blocks=blocks
        self.var_globals=var_globals
        self.code_funcs=code_funcs
        self.module = self.engine.module
        self.types={ 
                    "int":  ir.IntType(32),
                    "float":ir.DoubleType(),
                    "void": ir.VoidType(),
                    "char": ir.IntType(8)
                    }

        self.treat={
                    "add"       :   self.treat_op_math,
                    "sub"       :   self.treat_op_math,
                    "mul"       :   self.treat_op_math,
                    "div"       :   self.treat_op_math,
                    "mod"       :   self.treat_op_math,
                    "store"     :   self.treat_store,
                    "load"      :   self.treat_load,
                    "literal"   :   self.treat_literal,
                    "alloc"     :   self.treat_alloc,
                    "ne"        :   self.treat_comp,
                    "gq"        :   self.treat_comp,
                    "gt"        :   self.treat_comp,
                    "eq"        :   self.treat_comp,
                    "lt"        :   self.treat_comp,
                    "le"        :   self.treat_comp,
                    "bg"        :   self.treat_comp,
                    "and"       :   self.treat_logical,
                    "or"        :   self.treat_logical,
                    "cbranch"   :   self.treat_cbranch,
                    "jump"      :   self.treat_jump,
                    "return"    :   self.treat_return,
                    "print"     :   self.treat_print,
                    "define"    :   self.treat_define,
                    "call"      :   self.treat_call,
                    "param"     :   self.treat_param,
                    "elem"      :   self.treat_elem,
                    "sitofp"    :   self.treat_conversion,
                    "fptosi"    :   self.treat_conversion
                    }
        self.math_op={ 
                    "add_int"   :    'add'    ,
                    "add_float" :    'fadd'   ,
                    "sub_int"   :    'sub'    ,
                    "sub_float" :    'fsub'   ,
                    "div_int"   :    'sdiv'   ,
                    "div_float" :    'fdiv'   ,
                    "mul_int"   :    'mul'    ,
                    "mul_float" :    'fmul'   ,
                    "mod_int"   :    'srem'   ,
                    "mod_float" :    'frem'           
                    }
        self.binary={
            'lt'        :   '<',
            'le'        :   '<=',
            'gt'        :    '>',
            'gq'        :   '>=',
            'ne'        :   '!=',
            'or'        :   '||',
            'eq'        :   '==',
            'and'       :   '&&',
            }

    
        self.vars_globals=dict()
        self.vars=dict()
        self.builder=None
        self.func = None
        self.funcs=dict()
        self.blocks_llvm=dict()
        self.funcoes=[]
        self.args_call=[]
        self._declare_scanf_function()
        self._declare_printf_function()
        self.gen_llvm()

    def gen_llvm(self):
        #fnty = ir.FunctionType(ir.IntType(32), [ir.IntType(32)])
        for inst in self.var_globals:            
            self._treat_global(inst)
        for inst in self.code_funcs:
            _str=inst[0].split("_")    
            if(len(inst)>1):
                assert self.treat.get(_str[0])!=None ,f'{inst}'
                self.treat.get(_str[0])(inst)
            elif("return"==_str[0]): 
                self.treat_return(inst)   
            else:
                self.treat_label(inst)
        
        '''for f in self.funcoes:
            print(f)        
        self.engine.execute_ir()
        '''     
    def _treat_global(self,inst):
        #class llvmlite.ir.GlobalVariable(module, typ, name, addrspace=0)
        _str=inst[0].split("_")
        type=_str[1]
        dim=1
        if(len(_str)>2):
            for i in _str[2:]:
                dim*=int(i)
            var=ir.GlobalVariable(self.module, ir.ArrayType(self.types[type], dim), name=inst[1], addrspace=0)
            self.vars_globals[inst[1]]=var
        elif type == "string":
            cte = self.make_bytearray((inst[2] + "\00").encode('utf-8'))
            var = ir.GlobalVariable(self.module, cte.type, inst[1])
            var.initializer = cte
            var.align = 1
            var.global_constant = True
            self.vars_globals[inst[1]]=var
        elif(len(inst)==3 and isinstance(inst[2],tuple)):
            #Uma funçao
            self.creat_func(inst)    
        else:
            var = ir.GlobalVariable(self.module,self.types[type] , name=inst[1], addrspace=0)
            var.initializer=ir.Constant(self.types[type], inst[2])
            self.vars_globals[inst[1]]=var
    def treat_define(self,inst):
        _str=inst[0].split("_")
        self.vars=dict()
        self.vars.update(self.vars_globals)
        self.blocks_llvm=dict()
        self.func=self.creat_func(inst)
        for i,v in enumerate(inst[2]):  self.vars[v[1]]=self.func.args[i]


        self.blocks_llvm['%entry']=self.func.append_basic_block('%entry')
        self.builder=ir.IRBuilder(self.blocks_llvm['%entry'])
        self.create_basic_blocks()

    def creat_func(self,inst):
        _str=inst[0].split("_")
        fn=self.funcs.get(inst[1])
        if(not fn):
            ftype = ir.FunctionType(self.types[_str[1]], [self.types[v[0]] for v in inst[2] if v[0]!=None ])
            fn = ir.Function(self.module, ftype, inst[1][1:])
            self.funcs[inst[1]]=fn
            self.funcoes.append(fn)
            for i,v in enumerate(inst[2]):      fn.args[i].name= v[1]
        return fn
    
    def create_basic_blocks(self):
        blocks=self.blocks.retira()
        for block in blocks[1:]:
            name=block.instructions[0][0]
            name="%"+name
            self.blocks_llvm[name]=self.func.append_basic_block(name)    
    def treat_label(self,inst):
        self.builder.position_at_end(self.blocks_llvm["%"+inst[0]])
    def treat_alloc(self,inst):
        _str=inst[0].split("_")
        type=_str[1]
        if(len(_str)==2):
            # class llvmlite.ir.FloatType or class llvmlite.ir.IntType 
            var = self.builder.alloca(self.types[type], name=inst[1])
        elif(_str[2]=="*"):
            #class llvmlite.ir.PointerType(pointee, addrspace=0)
            _type=ir.PointerType(self.types[type], addrspace=0)
            var=self.builder.alloca(_type, name=inst[1])
            
        else:
            #class llvmlite.ir.ArrayType(element, count)
            dim=1
            for i in _str[2:]:  dim*=int(i)
            _type=ir.ArrayType(self.types[type], dim)
            var=self.builder.alloca(_type, name=inst[1])
        self.vars[inst[1]]=var
    def treat_store(self,inst):
        var1=self.vars[inst[1]]
        var2=self.vars[inst[2]]
        self.builder.store(var1, var2)
    def treat_load(self,inst):
        var=self.vars[inst[1]]     
        #_pointee = var.type.pointee
        res=self.builder.load(var, name=inst[2], align=None)
        if(not self.vars.get(inst[2])): self.vars[inst[2]]=res
    def treat_literal(self,inst):
        _str=inst[0].split("_")
        #char
        if(_str[1]=='char'):
            value=inst[1]
            value = int.from_bytes(value.encode('ascii'), byteorder='big')
            self.vars[inst[2]]=ir.Constant(self.types[_str[1]], value)
        else:
            self.vars[inst[2]]=ir.Constant(self.types[_str[1]], inst[1])
    def treat_op_math(self,inst):
        res=getattr(self.builder,self.math_op[inst[0]])(self.vars[inst[1]], self.vars[inst[2]], name=inst[3], flags=())
        self.vars[inst[3]]=res     
    def treat_comp(self,inst):
        _str=inst[0].split("_") 
        if(_str[1]=="int" or _str[1]=="bool"): 
            self.vars[inst[3]]=self.builder.icmp_signed(self.binary[_str[0]], self.vars[inst[1]], self.vars[inst[2]], name=inst[3])
        elif(_str[1]=="float"):
            self.vars[inst[3]]=self.builder.fcmp_ordered(self.binary[_str[0]], self.vars[inst[1]], self.vars[inst[2]], name=inst[3])
        else:
            assert 1==2,f'nao tratei {inst}'
    def treat_logical(self,inst):
        _str=inst[0].split("_")
        if(_str[0]=="and"):
            self.vars[inst[3]]=self.builder.and_(self.vars[inst[1]],self.vars[inst[2]],name=inst[3],flags=())
        elif(_str[0]=="or"):
            self.vars[inst[3]]=self.builder.or_(self.vars[inst[1]],self.vars[inst[2]],name=inst[3],flags=())

        else:
            pass
    def treat_read(self, var_type, target):
        _target = self.vars[target]
        if var_type == 'int':
            self._cio('scanf', '%d', _target)
        elif var_type == 'float':
            self._cio('scanf', '%lf', _target)
        elif var_type == 'char':
            self._cio('scanf', '%c', _target)

   
    def treat_cbranch(self,inst):
        self.builder.cbranch(self.vars[inst[1]], self.blocks_llvm[inst[2]], self.blocks_llvm[inst[3]])
    def treat_jump(self,inst):
        self.builder.branch(self.blocks_llvm[inst[1]])        
    def treat_return(self,inst):
        _str=inst[0].split("_")
        if(_str[1]!="void"):    self.builder.ret(self.vars[inst[1]])
        else:                   self.builder.ret_void()
        
    def treat_print(self, inst):
        #print(self.vars)
        
        _str=inst[0].split("_")
        val_type=_str[1]
        target=inst[1]
        if target:
            _value = self.vars[target]
            if val_type == 'int':
                self._cio('printf', '%d', _value)
            elif val_type == 'float':
                self._cio('printf', '%.2f', _value)
            elif val_type == 'char':
                self._cio('printf', '%c', _value)
            elif val_type == 'string':
                self._cio('printf', '%s', _value)
        else:
            self._cio('printf', '\n')
    def _cio(self, fname, format, *target):
        mod = self.builder.module
        fmt_bytes = self.make_bytearray((format + '\00').encode('ascii'))
        global_fmt = self._global_constant(mod, mod.get_unique_name('.fmt'), fmt_bytes)
        fn = mod.get_global(fname)
        ptr_fmt = self.builder.bitcast(global_fmt,ir.IntType(8).as_pointer())
        return self.builder.call(fn, [ptr_fmt] + list(target))
    def _global_constant(self, builder_or_module, name, value, linkage='internal'):
        
        if isinstance(builder_or_module, ir.Module):
            mod = builder_or_module
        else:
            mod = builder_or_module.module
        data = ir.GlobalVariable(self.module, value.type, name=name)
        data.linkage = linkage
        data.global_constant = True
        data.initializer = value
        data.align = 1
        return data
    def make_bytearray(self,buf):
        b = bytearray(buf)
        n = len(b)
        return ir.Constant(ir.ArrayType(ir.IntType(8), n), b)

    def treat_call(self,inst):
        # IRBuilder.call(fn, args, name='', cconv=None, tail=False, fastmath=())
        #print(self.args_call)
        try:
            self.vars[inst[2]]=self.builder.call(self.funcs[inst[1]], self.args_call, name=inst[2], cconv=None, tail=False, fastmath=())
            self.args_call=[]
        except KeyError:
            pass

    def treat_param(self,inst):
        self.args_call.append(self.vars[inst[1]])
    def treat_elem(self,inst):
        # IRBuilder.gep(ptr, indices, inbounds=False, name='')
        self.vars[inst[3]]=self.builder.gep(self.vars[inst[1]], [self.vars[inst[2]]], inbounds=False, name=inst[3])
    def treat_conversion(self,inst):
        _str=inst[0].split()
        if(_str[0]=="sitofp"):
            self.vars[inst[2]]=self.builder.sitofp(self.vars[inst[1]], typ=self.types["float"], name=inst[2])
        else:
            self.vars[inst[2]]=self.builder.fptosi(self.vars[inst[1]], typ=self.types["int"], name=inst[2])
    
    def _declare_printf_function(self):
        voidptr_ty = ir.IntType(8).as_pointer()
        printf_ty = ir.FunctionType(ir.IntType(32), [voidptr_ty], var_arg=True)
        printf = ir.Function(self.module, printf_ty, name="printf")
        self.printf = printf

    def _declare_scanf_function(self):
        voidptr_ty = ir.IntType(8).as_pointer()
        scanf_ty = ir.FunctionType(ir.IntType(32), [voidptr_ty], var_arg=True)
        scanf = ir.Function(self.module, scanf_ty, name="scanf")
        self.scanf = scanf

    def _cio(self, fname, format, *target):
        mod = self.builder.module
        fmt_bytes = self.make_bytearray((format + '\00').encode('ascii'))
        global_fmt = self._global_constant(mod, mod.get_unique_name('.fmt'), fmt_bytes)
        fn = mod.get_global(fname)
        ptr_fmt = self.builder.bitcast(global_fmt, ir.IntType(8).as_pointer())
        return self.builder.call(fn, [ptr_fmt] + list(target))

    def _global_constant(self, builder_or_module, name, value, linkage='internal'):

        if isinstance(builder_or_module, ir.Module):
            mod = builder_or_module
        else:
            mod = builder_or_module.module
        data = ir.GlobalVariable(mod, value.type, name=name)
        data.linkage = linkage
        data.global_constant = True
        data.initializer = value
        data.align = 1
        return data
    

    
