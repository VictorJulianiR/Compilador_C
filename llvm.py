from llvmlite import ir, binding
from ctypes import CFUNCTYPE, c_int
from engine_llvm import *
class LLVMFunctionVisitor():
    def __init__(self,blocks,var_globals,code_funcs):

        self.engine=Engine_LLVM()
        self.blocks=blocks
        self.var_globals=var_globals
        self.code_funcs=code_funcs
        self.module = self.engine.module
        self.types={ 
                    "int":  ir.IntType(32),
                    "float":ir.FloatType,
                    "void": ir.VoidType
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
                    "elem"      :   self.treat_elem
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
            'gt'        :   '>=',
            'ne'        :   '!=',
            'or'        :   '||',
            'eq'        :   '==',
            'and'       :   '&&',
            }

        
        int_ty = ir.IntType(32)
        i64_ty = ir.IntType(64)
        float_ty = ir.DoubleType()
        char_ty = ir.IntType(8)
        bool_ty = ir.IntType(1)
        void_ty = ir.VoidType()

        intptr_ty = int_ty.as_pointer()
        floatptr_ty = float_ty.as_pointer()
        charptr_ty = char_ty.as_pointer()
        voidptr_ty = char_ty.as_pointer()

        llvm_type = {'int': int_ty,
                    'int_*': intptr_ty,
                    'float': float_ty,
                    'float_*': floatptr_ty,
                    'char': char_ty,
                    'char_*': charptr_ty,
                    'void': void_ty,
                    'void_*': voidptr_ty,
                    'string': charptr_ty}

        llvm_false = ir.Constant(bool_ty, False)
        llvm_true = ir.Constant(bool_ty, True)


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
    
    def _get_global(self,inst):
        #class llvmlite.ir.GlobalVariable(module, typ, name, addrspace=0)
        _str=inst[0].split("_")
        type=_str[1]
        dim=1
        if(len(_str)>2):
            for i in _str[2:]:
                dim*=int(i)
            return ir.GlobalVariable(self.module, ir.ArrayType(self.types[type], dim), name=inst[1], addrspace=0)
        elif type == "string":
                cte = self.make_bytearray((inst[2] + "\00").encode('utf-8'))
                var = ir.GlobalVariable(self.module, cte.type, inst[1])
                var.initializer = cte
                var.align = 1
                var.global_constant = True
                return var
                
        else:
            var = ir.GlobalVariable(self.module,self.types[type] , name=inst[1], addrspace=0)
            var.initializer=ir.Constant(self.types[type], inst[2])
            return var


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


    def gen_llvm(self):
        #fnty = ir.FunctionType(ir.IntType(32), [ir.IntType(32)])
        for inst in self.var_globals:
            # class llvmlite.ir.GlobalVariable(module, typ, name, addrspace=0)
            
            var=self._get_global(inst)
            self.vars_globals[inst[1]]=var
        

        for inst in self.code_funcs:
            print(inst)
            if(len(inst)>1):
                _str=inst[0].split("_")    
                assert self.treat.get(_str[0])!=None ,f'{inst}'
                self.treat.get(_str[0])(inst)
            else:   self.treat_label(inst)
        
        for f in self.funcoes:
            print(f)
        self.engine.execute_ir()
                
    def treat_define(self,inst):
        _str=inst[0].split("_")
        self.vars=dict()
        self.vars.update(self.vars_globals)

        fnty = ir.FunctionType(self.types[_str[1]], [self.types[v[0]] for v in inst[2] if v[0]!=None ])
        fn = ir.Function(self.module, fnty, inst[1][1:])
        self.funcs[inst[1]]=fn
        self.funcoes.append(fn)

       
        for i,v in enumerate(inst[2]):  
            fn.args[i].name= v[1]
            self.vars[v[1]]=fn.args[i]
        self.func=fn
        self.blocks_llvm=dict()
        self.blocks_llvm['%entry']=self.func.append_basic_block('%entry')
        self.builder=ir.IRBuilder(self.blocks_llvm['%entry'])
        self.create_basic_blocks()
    def create_basic_blocks(self):
        blocks=self.blocks.desempilha()
        for block in blocks[1:]:
            name=block.instructions[0][0]
            if(name.isdigit()):  name="%"+name
            self.blocks_llvm[name]=self.func.append_basic_block(name)    
        print(self.blocks_llvm)       
        #builder = ir.IRBuilder(fn.append_basic_block('entry'))
    def treat_label(self,inst):
        if(inst[0].isdigit()):  self.builder.position_at_end(self.blocks_llvm["%"+inst[0]])
        else:                   self.builder.position_at_end(self.blocks_llvm[inst[0]])
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
        #print("to no load",inst ,self.vars.get(inst[2]))
        if(self.vars.get(inst[2])==None):     self.vars[inst[2]]=res
    def treat_literal(self,inst):
        _str=inst[0].split("_")
        self.vars[inst[2]]=ir.Constant(self.types[_str[1]], inst[1])
    def treat_op_math(self,inst):
        res=getattr(self.builder,self.math_op[inst[0]])(self.vars[inst[1]], self.vars[inst[2]], name=inst[3], flags=())
        self.vars[inst[3]]=res     
    def treat_comp(self,inst):
        _str=inst[0].split("_") 
        if(_str[1]=="int" or _str[1]=="bool"): 
            print(self.vars[inst[1]],self.vars[inst[2]])
            self.vars[inst[3]]=self.builder.icmp_signed(self.binary[_str[0]], self.vars[inst[1]], self.vars[inst[2]], name=inst[3])
        elif(_str[1]=="float"):
            self.vars[inst[3]]=self.builder.fcmp_ordered(self.binary[_str[0]], self.vars[inst[1]], self.vars[inst[2]], name=inst[3])
        else:
            assert 1==2,f'nao tratei {inst}'
    def treat_logical(self,inst):
        _str=inst[0].split("_")
        print(inst)
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
        print(self.blocks_llvm)
        self.builder.cbranch(self.vars[inst[1]], self.blocks_llvm[inst[2]], self.blocks_llvm[inst[3]])
    def treat_jump(self,inst):
        self.builder.branch(self.blocks_llvm[inst[1]])        
    def treat_return(self,inst):
        _str=inst[0].split("_")
        if(_str[1]!="void"):    self.builder.ret(self.vars[inst[1]])
        else:                   self.builder.ret_void()
        
    def treat_print(self, inst):
        
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
        self.vars[inst[2]]=self.builder.call(self.funcs[inst[1]], self.args_call, name=inst[2], cconv=None, tail=False, fastmath=())
        self.args_call=[]
    
    '''def _build_call(self, ret_type, name, target):
        if name == '%':
            _loc = self.builder.call(self._get_loc(name), self.params)
        else:
            try:
                _fn = self.builder.module.get_global(name[1:])
            except KeyError:
                _type = llvm_type[ret_type]
                _sig = [arg.type for arg in self.params]
                funty = ir.FunctionType(_type, _sig)
                _fn = ir.Function(self.module, funty, name=name[1:])
            _loc = self.builder.call(_fn, self.params)
        self.loc[target] = _loc
        self.params = []
    '''
        
    def treat_param(self,inst):
        self.args_call.append(self.vars[inst[1]])
    def treat_elem(self,inst):
        # IRBuilder.gep(ptr, indices, inbounds=False, name='')
        self.vars[inst[3]]=self.builder.gep(self.vars[inst[1]], [self.vars[inst[2]]], inbounds=False, name=inst[3])

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

    def get_align(ltype, width):
        if isinstance(ltype, ir.IntType):
            return ltype.width // 8
        elif isinstance(ltype, ir.DoubleType) or isinstance(ltype, ir.PointerType):
            return 8
        elif isinstance(ltype, ir.ArrayType):
            _align = self.get_align(ltype.element, 1)
            if width < 4:
                width = 1
            else:
                width = 4
            return _align * width


    

'''
    def _generate_global_instructions(self, glbInst):
        for inst in glbInst:
            _ctype, _modifier = self._extract_global_operation(inst[0])
            _type = llvm_type[_ctype]
            _name = inst[1][1:]
            _value = inst[2]
            fn_sig = isinstance(_value, list)
            if fn_sig:
                for _el in _value:
                    if _el not in list(llvm_type.keys()):
                        fn_sig = False
            if _ctype == "string":
                cte = self.make_bytearray((_value + "\00").encode('utf-8'))
                gv = ir.GlobalVariable(self.module, cte.type, _name)
                gv.initializer = cte
                gv.align = 1
                gv.global_constant = True
            elif _modifier and not fn_sig:
                _width = 4
                for arg in reversed(list(_modifier.values())):
                    if arg.isdigit():
                        _width = int(arg)
                        _type = ir.ArrayType(_type, int(arg))
                    else:
                        _type = ir.PointerType(_type)
                gv = ir.GlobalVariable(self.module, _type, _name)
                gv.initializer = ir.Constant(_type, _value)
                gv.align = get_align(_type, _width)
                if _name.startswith('.const'):
                    gv.global_constant = True
                elif fn_sig:
                    _sig = [llvm_type[arg] for arg in _value]
                    funty = ir.FunctionType(llvm_type[_ctype], _sig)
                    gv = ir.GlobalVariable(self.module, funty.as_pointer(), _name)
                    gv.linkage = 'common'
                    gv.initializer = ir.Constant(funty.as_pointer(), None)
                    gv.align = 8
                else:
                    gv = ir.GlobalVariable(self.module, _type, _name)
                    gv.align = get_align(_type, 1)
                    if _value:
                        gv.initializer = ir.Constant(_type, _value)
    def _extract_global_operation(self, source):
        _modifier = {}
        _aux = source.split('_')
        assert _aux[0] == 'global'
        _ctype = _aux[1]
        assert _ctype in ('int', 'float', 'char', 'string')
        if len(_aux) > 2:
            _val = _aux[2]
            if _val.isdigit():
                _modifier['dim_1'] = _val
            elif _val == "*":
                _modifier['ptr_1'] = _val
        if len(_aux) > 3:
            _val = _aux[3]
            if _val.isdigit():
                _modifier['dim_2'] = _val
            elif _val == "*":
                _modifier['ptr_2'] = _val
        return (_ctype, _modifier)
'''
