from graphviz import Digraph

class Block(object):
    def __init__(self, label):
        self.label = label       # Label that identifies the block
        self.instructions = []   # Instructions in the block
        self.predecessors = []   # List of predecessors    
        self.next_block = None  # Not necessary the same as next_block in the linked list
        self.visit = False
    
        self.gen=0
        self.kill=0
        self.gdefs=dict()
        self.r_IN=0
        self.r_OUT=0
        self.cop_var_var=dict()
       
        self.l_IN=set()
        self.l_OUT=set()
        self.use=set()
        self.dfs=set()
       
    def append(self,line,inst):
        self.instructions.append(inst)
      
    def __iter__(self):
        return iter(self.instructions)
        
    
    def changeClass(self,obj,obj_change):
        #trocar a classe em tempo de execução
        obj.__class__ = obj_change

class ConditionBlock(Block):
    """
    Class for a block representing an conditional statement.
    There are two branches to handle each possibility.
    """
    def __init__(self, label):
        super(ConditionBlock, self).__init__(label)
        self.fall_through = None

    
class BlockVisitor(object):
    '''
    Class for visiting basic blocks.  Define a subclass and define
    methods such as visit_BasicBlock or visit_IfBlock to implement
    custom processing (similar to ASTs).
    '''
    def visit(self,block):
        if( not isinstance(block, Block) or block.visit ):         return
        block.visit=True
        name = "visit_%s" % type(block).__name__
        if hasattr(self, name):
            getattr(self, name)(block)
        self.visit(block.next_block)
        if(isinstance(block, ConditionBlock)):
            self.visit(block.fall_through)
    def get_blocks(self,block,blocks):
        if( not isinstance(block, Block) or block.visit ):         return
        block.visit=True
        blocks.append(block)#Essa linha pega os blocks
        self.get_blocks(block.next_block,blocks)
        if(isinstance(block, ConditionBlock)):
            self.get_blocks(block.fall_through,blocks)


def format_instruction(t):
    # Auxiliary method to pretty print the instructions 
    op = t[0]
    if(op==None): return None
    if len(t) > 1:
        if op == "define":
            return f"\n{op} {t[1]}"
        else:
            _str = "" if op.startswith('global') else "  "
            if op == 'jump':
                _str += f"{op} label {t[1]}"
            elif op == 'cbranch':
                _str += f"{op} {t[1]} label {t[2]} label {t[3]}"
            elif op == 'global_string':
                _str += f"{op} {t[1]} \'{t[2]}\'"
            elif op.startswith('return'):
                _str += f"{op} {t[1]}"
            else:
                for _el in t:
                    _str += f"{_el} "
            return _str
    elif op == 'print_void' or op == 'return_void':
        return f"  {op}"
    else:
        return f"{op}"
class CFG(object):

    def __init__(self, fname):
        self.fname = fname
        self.g = Digraph('g', filename=fname + '.gv', node_attr={'shape': 'record'})
    #.next_block
    def visit_Block(self, block):
        # Get the label as node name
        _name = block.label
        if _name:
            # get the formatted instructions as node label
            _label = "{" + _name + ":\l\t"
            for _inst in block.instructions[1:]:

                if(_inst[0]): _label += format_instruction(_inst) + "\l\t"
            _label += "}"
            self.g.node(_name, label=_label)
            if block.next_block:
                self.g.edge(_name, block.next_block.label)
        else:
            # Function definition. An empty block that connect to the Entry Block
            self.g.node(self.fname, label=None, _attributes={'shape': 'ellipse'})
            self.g.edge(self.fname, block.next_block.label)

    def visit_ConditionBlock(self, block):
        # Get the label as node name
        _name = block.label
        # get the formatted instructions as node label
        _label = "{" + _name + ":\l\t"
        for _inst in block.instructions[1:]:
            if(_inst[0]):    _label += format_instruction(_inst) + "\l\t"
        _label +="|{<f0>T|<f1>F}}"
        self.g.node(_name, label=_label)
        self.g.edge(_name + ":f0", block.next_block.label)
        self.g.edge(_name + ":f1", block.fall_through.label)


    def view(self, block):
        self.deep_view(block)
        self.g.view()
    def deep_view(self,block):
        if( not isinstance(block, Block) or block.visit ):         return
        block.visit=True
        name = "visit_%s" % type(block).__name__
        if hasattr(self, name):
            getattr(self, name)(block)
        self.deep_view(block.next_block)
        if(isinstance(block, ConditionBlock)):
            self.deep_view(block.fall_through)


