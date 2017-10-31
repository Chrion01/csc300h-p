import sys
from pycparser import parse_file
import pycparser.c_ast as pc
from minic.minic_ast import *


class LoopVisitor(NodeVisitor):
    def __init__(self):
        self.nodes = []
        self.loop_vars = []

    def visit_For(self, For):

        self.nodes.append(For)
        b_vist = BodyVisitor()
        b_vist.visit(For)
        self.loop_vars.append(b_vist.values)

    def visit_While(self, While):
        self.nodes.append(While)
        b_vist = BodyVisitor()
        b_vist.visit(While)
        self.loop_vars.append(b_vist.values)

class BodyVisitor(NodeVisitor):

    def __init__(self):
        self.values = []
        self.decls = []

    def visit_Assignment(self, assignment):
        if not assignment.lvalue.name in self.values:
            self.values.append(assignment.lvalue.name)

    def visit_BinaryOp(self, binaryOp):
        if isinstance(binaryOp.right, pc.ID) and not(binaryOp.right.name in self.decls):
            if not binaryOp.right.name in self.values:
                self.values.append(binaryOp.right.name)
        if isinstance(binaryOp.left, pc.ID) and not(binaryOp.left.name in self.decls):
            if not binaryOp.left.name in self.values:
                self.values.append(binaryOp.left.name)
        else:
            self.visit(binaryOp.left)
            self.visit(binaryOp.right)

    def visit_Decl(self, decl):
        if not decl.name in self.decls:
            self.decls.append(decl.name)

class ConstantVisitor(NodeVisitor):
    def __init__(self):
        self.values = []

    def visit_Constant(self, node):
        print('Const\n')
        self.values.append(node.value)

class LoopReach(NodeVisitor):

    def __init__(self, vars):
        self.target_vars = vars
        self.expressions = []
        self.expressions_after = []
        self.loop_reached = False

    # def visit_TypeDecl(self, decl):
    #     if decl.declname in self.target_vars:
    #         self.expressions.append(decl)
    #         decl.show()
    def visit_For(self, For):
        self.loop_reached = True

    def visit_Decl(self, decl):
        # if isinstance(decl.type, pc.FuncDecl):
        #     print(decl.type)
        if not isinstance(decl.type, pc.FuncDecl) \
                and decl.name in self.target_vars \
                and not self.loop_reached:
            self.expressions.append(decl)
            #decl.show()

        if not isinstance(decl.type, pc.FuncDecl) \
                and decl.name in self.target_vars \
                and self.loop_reached:
            self.expressions_after.append(decl)
            decl.show()

if __name__ == '__main__':
    ast = parse_file('./tests/c_files/minic.c')

    n_vist = LoopVisitor()
    n_vist.visit(ast)

    print("loop vars: {}".format(n_vist.loop_vars))
    print("loops    : {}".format(n_vist.nodes))

    loop_var_reach = LoopReach(n_vist.loop_vars)
    loop_var_reach.visit(ast)

    print("loop reach vars: {}".format(loop_var_reach.expressions))
    print("post vars: {}".format(loop_var_reach.expressions_after))

    #loop_var_reach.expressions[0].show()

    exit(0)