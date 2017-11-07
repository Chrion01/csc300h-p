import sys
from pycparser import parse_file
import pycparser.c_ast as pc
from minic.minic_ast import *
from minic.c_ast_to_minic import *


class LoopVisitor(NodeVisitor):

    def __init__(self):
        self.nodes = []
        self.loop_vars = []
        self.reads = []
        self.writes = []
        self.array_index = []

    def visit_For(self, For):
        self.nodes.append(For)
        b_vist = BodyVisitor()
        b_vist.visit(For)
        self.loop_vars.append(b_vist.values[:])
        self.reads.append(b_vist.reads[:])
        self.writes.append(b_vist.writes[:])
        array_in_mod = FindModifiers(b_vist.array_indexes)
        array_in_mod.visit(For)
        self.array_index.append(array_in_mod.modifiers)

    def visit_While(self, While):
        self.nodes.append(While)
        b_vist = BodyVisitor()
        b_vist.visit(While)
        self.loop_vars.append(b_vist.values[:])
        self.reads.append(b_vist.reads[:])
        self.writes.append(b_vist.writes[:])
        array_in_mod = FindModifiers(b_vist.array_indexes)
        array_in_mod.visit(While)
        self.array_index.append(array_in_mod.modifiers)

class BodyVisitor(NodeVisitor):

    def __init__(self):
        self.values = []
        self.decls = []
        self.reads = []
        self.writes = []
        self.array_indexes = []

    def visit_Assignment(self, assignment):
        if isinstance(assignment.lvalue, pc.ID):
            if not assignment.lvalue.name in self.values:
                self.values.append(assignment.lvalue.name)
                self.writes.append(assignment.lvalue.name)
        elif isinstance(assignment.lvalue, pc.ArrayRef):
            self.writes.append(assignment.lvalue.name.name)
            self.array_indexes.append(assignment.lvalue.subscript.name)
        if isinstance(assignment.rvalue, pc.ID):
            self.reads.append(assignment.rvalue.name)
        elif isinstance(assignment.rvalue, pc.ArrayRef):
            self.reads.append(assignment.rvalue.name.name)
        else:
            self.visit(assignment.rvalue)


    def visit_BinaryOp(self, binaryOp):
        if isinstance(binaryOp.right, pc.ID):
            if binaryOp.right.name not in self.values and not(binaryOp.right.name in self.decls):
                self.values.append(binaryOp.right.name)
                self.reads.append(binaryOp.right.name)
        else:
            self.visit(binaryOp.right)
        if isinstance(binaryOp.left, pc.ID):
            if binaryOp.left.name not in self.values and not(binaryOp.left.name in self.decls):
                self.values.append(binaryOp.left.name)
                self.reads.append(binaryOp.left.name)
        else:
            self.visit(binaryOp.left)

    def visit_Decl(self, decl):
        if not decl.name in self.decls:
            self.decls.append(decl.name)

    def visit_UnaryOp(self, unary):
        if isinstance(unary.expr, pc.ID) and not(unary.expr.name in self.decls):
            self.values.append(unary.expr.name)
            self.writes.append(unary.expr.name)





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
        self.loop_count = len(nodes)
        

    def visit_For(self,node):
        self.generic_visit(node)
        self.index += 1
        self.passed[self.index] = True

    def visit_While(self, node):
        self.generic_visit(node)
        self.index += 1
        self.passed[self.index] = True        

    def visit_BinaryOp(self, binaryOp):

        if(self.index != -1):
            if isinstance(binaryOp.right, pc.ID):
                for i in range(self.loop_count):
                    if self.passed[i]:
                        if binaryOp.right.name in self.target_vars[i]:
                            temp = self.live_vars[i][:]
                            temp.append(binaryOp.right.name)
                            self.live_vars[i] = temp[:]
                            self.target_vars[i].remove(binaryOp.right.name)
            else:
                self.visit(binaryOp.right)
            if isinstance(binaryOp.left, pc.ID):
                for i in range(self.loop_count):
                    if self.passed[i]:
                        if binaryOp.left.name in self.target_vars[i]:
                            temp = self.live_vars[i][:]
                            temp.append(binaryOp.left.name)
                            self.live_vars[i] = temp[:]
                            self.target_vars[i].remove(binaryOp.left.name)
            else:
                self.visit(binaryOp.left)

    def visit_Assignment(self,node):
        if(self.index != -1):
            if isinstance(node.rvalue, pc.ID):
                for i in range(0, self.index + 1):
                    # for var in self.target_vars[i]:
                    #     if (var == node.rvalue.name):
                    #         self.live_vars[i].append(var)
                    if node.rvalue.name in self.target_vars[i]:
                        temp = self.live_vars[i][:]
                        
                        temp.append(node.rvalue.name)
                        self.live_vars[i] = temp[:]
            else:
                self.visit(node.rvalue)            
            if node.op == '=':          
                if isinstance(node.lvalue, pc.ID):
                    for i in range(0, self.index + 1):
                        temp = []
                        for var in self.target_vars[i]:
                            if (var != node.lvalue.name):
                                temp.append(var)
                        self.target_vars[i] = temp[:]
            else:
                if isinstance(node.lvalue, pc.ID):
                    for i in range(self.loop_count): 
                        if self.passed[i] and node.lvalue.name in self.target_vars[i]:
                            temp = self.live_vars[i][:]
                            temp.append(node.lvalue.name)
                            self.live_vars[i] = temp[:]
                            self.target_vars[i].remove(node.lvalue.name)

    def visit_Decl(self,node):
        if(self.index != -1):
            if not isinstance(node.type, pc.FuncDecl) and not isinstance(node.type, pc.PtrDecl):
                if isinstance(node.init, pc.ID):
                    for i in range(0, self.index + 1):
                        for var in self.target_vars[i]:
                            if (var == node.init.name):
                                print("DeclRight",node.init.name,i) 
                                print("before",self.live_vars)
                                temp = self.live_vars[i][:]
                        
                                temp.append(node.rvalue.name)
                                self.live_vars[i] = temp[:]
                                print("after",self.live_vars)                                
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
    
    
class FindModifiers(NodeVisitor):

    def __init__(self, variables):
        self.vars = variables
        self.modifiers = {}
        for var in self.vars:
            self.modifiers[var] = []

    def visit_UnaryOp(self, unary):
        if isinstance(unary.expr, pc.ID) and unary.expr.name in self.vars:
            self.modifiers[unary.expr.name].append(unary)

    def visit_Assignment(self, assignment):
        if isinstance(assignment.lvalue, pc.ID) and assignment.lvalue.name in self.vars:
            self.modifiers[assignment.lvalue.name].append(assignment)






                # def visit_

class FuncVisitor(NodeVisitor):

    def __init__(self):
        self.functions = []
        self.function_nodes = []
        self.function_loop_variables = []
        self.function_reach_defs = []
        self.function_live_vars = []

        self.loops = []

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

        lva = LiveVarAn(lv.loop_vars[:], lv.nodes[:])
        lva.visit(FuncDecl)
        self.function_live_vars.append(lva.live_vars[:])

        for i in range(len(lv.nodes)):
            loop = Loop(lv.nodes[i], lv.reads[i], lv.writes[i],
                        rl.loop_reach_definition[i], lva.live_vars[i], lv.array_index[i])
            self.loops.append(loop)


class Loop():
    def __init__(self, node, reads, writes, defs, live, array_ind):
        self.node = node
        self.read_variables = reads
        self.write_variables = writes
        self.reach_defs = defs
        self.live_vars = live
        self.array_ind = array_ind

    def __str__(self):
        defs = []
        for item in self.reach_defs:
            defs.append(transform(item).__str__())

        statement = "Read Variables: {}\n".format(self.read_variables) + \
                    "Write Variables: {}\n".format(self.write_variables) + \
                    "Reaching Def: {}\n".format(defs) + \
                    "Live Variables: {}\n".format(self.live_vars)
        for key in self.array_ind.keys():
            statement += "Array Index Var {}\n".format(key)
            for item in self.array_ind[key]:
                statement += "{}\n".format(transform(item).__str__())


        return statement

if __name__ == '__main__':
    ast = parse_file('./tests/c_files/minic.c')

    n_vist = FuncVisitor()
    n_vist.visit(ast)
    # print("functions: {}".format(n_vist.functions))
    # print("loops    : {}".format(n_vist.function_nodes))
    # print("loop vars: {}".format(n_vist.function_loop_variables))
    # print("loop reach vars: {}".format(n_vist.function_reach_defs))
    # print("loop live vars: {}".format(n_vist.function_live_vars))
    for loop in n_vist.loops:
        print(loop)

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

