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
        self.loop_vars.append(b_vist.values[:])

    def visit_While(self, While):
        self.nodes.append(While)
        b_vist = BodyVisitor()
        b_vist.visit(While)
        self.loop_vars.append(b_vist.values[:])

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

# class ConstantVisitor(NodeVisitor):
#     def __init__(self):
#         self.values = []
#
#     def visit_Constant(self, node):
#         print('Const\n')
#         self.values.append(node.value)

class LoopReach(NodeVisitor):

    def __init__(self, vars, nodes):
        self.target_vars = vars
        self.loops = nodes
        self.reach_definition = []
        self.loop_reach_definition = [[]] * len(nodes)
        self.expressions_after = [[]] * len(nodes)
        self.index = 0

    def visit_For(self, For):
        temp = []
        for exp in self.reach_definition:
            if isinstance(exp, pc.Decl):
                if exp.name in self.target_vars[self.index]:
                    temp.append(exp)
            elif isinstance(exp, pc.Assignment):
                if exp.lvalue.name in self.target_vars[self.index]:
                    temp.append(exp)
        self.loop_reach_definition[self.index] = temp[:]
        self.index += 1
        self.generic_visit(For)

    def visit_While(self, While):
        temp = []
        for exp in self.reach_definition:
            if isinstance(exp, pc.Decl):
                if exp.name in self.target_vars[self.index]:
                    temp.append(exp)
            elif isinstance(exp, pc.Assignment):
                if exp.lvalue.name in self.target_vars[self.index]:
                    temp.append(exp)
        self.loop_reach_definition[self.index] = temp[:]
        self.index += 1
        self.generic_visit(While)

    def visit_Decl(self, decl):
        if not isinstance(decl.type, pc.FuncDecl):
            name = decl.name
            temp = []
            for exp in self.reach_definition:
                if isinstance(exp, pc.Decl):
                    if exp.name != name:
                        temp.append(exp)
                elif isinstance(exp, pc.Assignment):
                    if exp.lvalue.name != name:
                        temp.append(exp)
            temp.append(decl)
            self.reach_definition = temp[:]

    def visit_Assignment(self, assign):
        name = assign.lvalue.name
        temp = []
        for exp in self.reach_definition:
            if isinstance(exp, pc.Decl):
                if exp.name != name:
                    temp.append(exp)
            elif isinstance(exp, pc.Assignment):
                if exp.lvalue.name != name:
                    temp.append(exp)
        temp.append(assign)
        self.reach_definition = temp[:]

class LiveVarAn(NodeVisitor):

    def __init__(self, vars, nodes):
        self.target_vars = vars
        self.loops = nodes
        self.live_vars = [[]] * len(nodes)
        self.passed = [False] * len(nodes)
        self.index = -1

    def visit_For(self,node):
        self.generic_visit(node)
        self.index += 1

    def visit_While(self, node):
        self.generic_visit(node)
        self.index += 1

    def visit_BinaryOp(self, binaryOp):
        if isinstance(binaryOp.right, pc.ID):
            for i in range(0,self.index+1):
                for var in  self.target_vars[i]:
                    if(var == binaryOp.right.name):
                       self.live_vars[i].append(var)
        if isinstance(binaryOp.left, pc.ID):
            for i in range(0,self.index+1):
                for var in  self.target_vars[i]:
                    if(var == binaryOp.left.name):
                       self.live_vars[i].append(var)
        else:
            self.visit(binaryOp.left)
            self.visit(binaryOp.right)

    def visit_Assignment(self,node):
        if isinstance(node.rvalue, pc.ID):
            for i in range(0, self.index + 1):
                # for var in self.target_vars[i]:
                #     if (var == node.rvalue.name):
                #         self.live_vars[i].append(var)
                if node.rvalue.name in self.target_vars[i]:
                    self.live_vars[i].append(node.rvalue.name)
        else:
            self.visit(node.rvalue)

        if isinstance(node.lvalue, pc.ID):
            for i in range(0, self.index + 1):
                temp = []
                for var in self.target_vars[i]:
                    if (var != node.lvalue.name):
                        temp.append(var)
                self.target_vars[i] = temp[:]

    def visit_Decl(self,node):
        if not isinstance(node.type, pc.FuncDecl) and not isinstance(node.type, pc.PtrDecl):
            if isinstance(node.init, pc.ID):
                for i in range(0, self.index + 1):
                    for var in self.target_vars[i]:
                        if (var == node.init.name):
                            self.live_vars[i].append(node.init.name)
            elif isinstance(node.init, pc.Constant):
                pass
            else:
                self.visit(node.init)

        if isinstance(node.name, pc.ID):
            for i in range(0, self.index + 1):
                temp = []
                for var in self.target_vars[i]:
                    if (var != node.name):
                        temp.append(var)
                self.target_vars[i] = temp[:]








                # def visit_

class FuncVisitor(NodeVisitor):

    def __init__(self):
        self.functions = []
        self.function_nodes = []
        self.function_loop_variables = []
        self.function_reach_defs = []
        self.function_live_vars = []


    def visit_FuncDef(self, FuncDecl):
        self.functions.append((FuncDecl.decl.name,FuncDecl))

        lv = LoopVisitor()
        lv.visit(FuncDecl)
        self.function_nodes.append(lv.nodes)
        self.function_loop_variables.append((FuncDecl.decl.name, lv.loop_vars))

        rl = LoopReach(lv.loop_vars, lv.nodes)
        rl.visit(FuncDecl)
        # combination = [rl.loop_reach_definition, rl.expressions_after]
        self.function_reach_defs.append(rl.loop_reach_definition)

        lv = LiveVarAn(lv.loop_vars, lv.nodes)
        lv.visit(FuncDecl)
        self.function_live_vars.append(lv.live_vars)





if __name__ == '__main__':
    ast = parse_file('./tests/c_files/minic.c')

    n_vist = FuncVisitor()
    n_vist.visit(ast)
    print("functions: {}".format(n_vist.functions))
    print("loops    : {}".format(n_vist.function_nodes))
    print("loop vars: {}".format(n_vist.function_loop_variables))
    print("loop reach vars: {}".format(n_vist.function_reach_defs))
    print("loop live vars: {}".format(n_vist.function_live_vars))
    # for function in n_vist.function_reach_defs:
    #     print("f")
    #     for loop in function:
    #         print('l')
    #         for exp in loop:
    #             if isinstance(exp, pc.Decl):
    #                 print('Decl: {} = {}'.format(exp.name, exp.init.value))
    #             elif isinstance(exp, pc.Assignment):
    #                 print('Asgn: {}'.format(exp.lvalue.name))

    # ast.show()

    # loop_var_reach = LoopReach(n_vist.loop_vars, n_vist.nodes)
    # loop_var_reach.visit(ast)
    #


    #loop_var_reach.expressions[0].show()

    exit(0)