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

    def __init__(self, vars, nodes):
        self.target_vars = vars
        self.loops = nodes
        self.expressions = [[]] * len(nodes)
        self.expressions_after = [[]] * len(nodes)
        self.loop_reached = [False] * len(nodes)
        self.index = 0

    def add_exp(self, expression):
        assert (isinstance(expression, pc.Decl))
        name = expression.name
        temp = []
        for exp in self.expressions[self.index]:
            if not exp.name == name:
                temp.append(exp)
        temp.append(expression)
        self.expressions[self.index] = temp[:]

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

class FuncVisitor(NodeVisitor):

    def __init__(self):
        self.functions = []
        self.function_nodes = []
        self.function_loop_variables = []
        self.function_reach_live = []

    def visit_FuncDef(self, FuncDecl):
        self.functions.append([FuncDecl.decl.name,FuncDecl])

        lv = LoopVisitor()
        lv.visit(FuncDecl)
        self.function_nodes.append(lv.nodes)
        self.function_loop_variables.append(lv.loop_vars)

        rl = LoopReach(lv.loop_vars, lv.nodes)
        rl.visit(FuncDecl)
        combination = [rl.expressions, rl.expressions_after]
        self.function_reach_live.append(combination)



if __name__ == '__main__':
    ast = parse_file('./tests/c_files/minic.c')

    n_vist = FuncVisitor()
    n_vist.visit(ast)
    print("functions: {}".format(n_vist.functions))
    print("loops    : {}".format(n_vist.function_nodes))
    print("loop vars: {}".format(n_vist.function_loop_variables))
    print("loop reach vars: {}".format(n_vist.function_reach_live))

    # loop_var_reach = LoopReach(n_vist.loop_vars, n_vist.nodes)
    # loop_var_reach.visit(ast)
    #


    #loop_var_reach.expressions[0].show()

    exit(0)