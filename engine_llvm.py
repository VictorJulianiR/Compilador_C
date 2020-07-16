from llvmlite import ir, binding
from ctypes import CFUNCTYPE, c_int

class Engine_LLVM():
    def __init__(self):
        self.binding = binding
        self.binding.initialize()
        self.binding.initialize_native_target()
        self.binding.initialize_native_asmprinter()
        
        #self.module = ir.Module(name=__file__)#Correto
        self.module = ir.Module()
        self.module.triple = self.binding.get_default_triple()
        self._create_execution_engine()
        
        # declare external functions
        
    def _create_execution_engine(self):
        """
        Create an ExecutionEngine suitable for JIT code generation on
        the host CPU.  The engine is reusable for an arbitrary number of
        modules.
        """
        target = self.binding.Target.from_default_triple()
        target_machine = target.create_target_machine()
        # And an execution engine with an empty backing module
        backing_mod = binding.parse_assembly("")
        engine = binding.create_mcjit_compiler(backing_mod, target_machine)
        self.engine = engine
    def _compile_ir(self):
        """
        Compile the LLVM IR string with the given engine.
        The compiled module object is returned.
        """
        # Create a LLVM module object from the IR
        llvm_ir = str(self.module)
        mod = self.binding.parse_assembly(llvm_ir)
        mod.verify()
        # Now add the module and make sure it is ready for execution
        self.engine.add_module(mod)
        self.engine.finalize_object()
        self.engine.run_static_constructors()
        return mod

    def save_ir(self, output_file):
        output_file.write(str(self.module))
            
    def execute_ir(self, opt=None, opt_file=None):
        mod = self._compile_ir()
        
        if self.opt:
            # apply some optimization passes on module
            pmb = self.binding.create_pass_manager_builder()
            pm = self.binding.create_module_pass_manager()
            pmb.opt_level = 0
            if opt == 'ctm' or opt == 'all':
                pm.add_constant_merge_pass()
            if opt == 'dce' or opt == 'all':
                pm.add_dead_code_elimination_pass()
            if opt == 'cfg' or opt  == 'all':
                pm.add_cfg_simplification_pass()
            pmb.populate(pm)
            pm.run(mod)
            opt_file.write(str(mod))
            
        # Obtain a pointer to the compiled 'main' - it's the address of its JITed code in memory.
        main_ptr = self.engine.get_function_address('main')
        # To convert an address to an actual callable thing we have to use
        # CFUNCTYPE, and specify the arguments & return type.
        main_function = CFUNCTYPE(c_int)(main_ptr)
        # Now 'main_function' is an actual callable we can invoke
        res = main_function()
        print(res)


