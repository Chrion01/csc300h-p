import sys
from pycparser import parse_file
import pycparser.c_ast as pc
from minic.minic_ast import *
from minic.c_ast_to_minic import *


class TopLoopFinder(NodeVisitor):

    def __init__(self):
        self.nodes = []
        self.nested = {}

    def visit_For(self, For):
        self.nodes.append(For)
        f_vis = LoopVisitor()
        f_vis.visit(For)
        if len(f_vis.index_vector) > 1:
            self.nested[For] = [f_vis.index_vector]
            # dv = DependenceCalc(f_vis.index_vector)
            # dv.visit(For)
            # self.nested[For].append(dv.dependencies)

    def __str__(self):
        res = ""
        for node in self.nested.keys():
            res += 'Loop nest: {}\n'.format(node)
            res += '\tIndex Vector: {}\n'.format(self.nested[node][0])
            res += '\tDependence vectors:\n'
            # deps = self.nested[node][1].keys()
            # for dep in deps:
            #     res += '\t\tStatement {} : D = {}\n'.format(dep, self.nested[node][1][dep])
        return res



class LoopVisitor(NodeVisitor):

    def __init__(self):
        self.nodes = []
        self.index_vector = []
        self.dependencyVector = {}

    def visit_Assignment(self, assignment):
        if isinstance(assignment.lvalue, pc.ArrayRef):
            # not finished half done
            n = 1
            Y = assignment.lvalue
            values = []
            IDS = []
            while(isinstance(Y.name,pc.ArrayRef)):
                g = Y.subscript
                if (isinstance(g, pc.ID)):
                    IDS.append(g.name)
                    values = values + [0]
                elif (isinstance(g, pc.BinaryOp)):
                    if (isinstance(g.right, pc.ID) and isinstance(g.left, pc.Constant)):
                        IDS.append(g.right.name)
                        if (g.op == "-"):
                            values = values + [-g.left.value]
                        elif (g.op == "+"):
                            values = values + [g.left.value]
                    if (isinstance(g.left, pc.ID) and isinstance(g.right, pc.Constant)):
                        IDS.append(g.left.name)
                        if (g.op == "-"):
                            values =  values + [-g.right.value]
                        elif (g.op == "+"):
                            values = values + [g.right.value]
                elif(isinstance(g,pc.Constant)):
                    values = values + [0]
                Y = Y.name
                n += 1
            kewl = DependenceCalc(Y.name,self.index_vector,n)
            R = assignment.rvalue
            G = []
            LhandValues = []
            Tr = isinstance(R,pc.ArrayRef)
            while(Tr and isinstance(R.name,pc.ArrayRef)):
                G.append(R.subscript)
                R = R.name
            if(isinstance(R,pc.ArrayRef) and Y.name == R.name):
                for g in G:
                    if(isinstance(g,pc.ID)):
                        LhandValues = LhandValues + [0]
                    elif(isinstance(g,pc.BinaryOp)):
                        if(isinstance(g.right,pc.ID) and isinstance(g.left,pc.Constant)):
                            if(g.op == "-"):
                                LhandValues = LhandValues +[-g.left.value]
                            elif(g.op == "+"):
                                LhandValues = LhandValues + [g.left.value]
                        if (isinstance(g.left, pc.ID) and isinstance(g.right, pc.Constant)):
                            if (g.op == "-"):
                                LhandValues = LhandValues + [-g.right.value]
                            elif (g.op == "+"):
                                LhandValues = LhandValues + [g.right.value]
                    elif(isinstance(g,pc.Constant)):
                        LhandValues = LhandValues + [0]

            elif isinstance(assignment.rvalue,pc.BinaryOp):
                kewl.visit(assignment.rvalue)



    def visit_For(self, For):
        # self.index_vector.append()
        kids = For.children()
        init = 0
        for kid in kids:
            if kid[0] == 'init' and isinstance(kids[0][1], pc.Assignment):
                init = kid[1]
        if init == 0:
            print("INDEX NOT FOUND FOR LOOP {}".format(transform(For).__str__()))
        else:
            index = kids[0][1]
            self.index_vector.append(index.lvalue.name)
            f_vis = LoopVisitor()
            for kid in kids:
                f_vis.visit(kid[1])
            self.index_vector += f_vis.index_vector


class DependenceCalc(NodeVisitor):
    def __init__(self,a,i,n):
        self.a = a
        self.i = i
        self.n = n
        self.depend = [[]*n]

    def visit_BinaryOp(self,binaryOp):
        if isinstance(binaryOp.right, pc.ArrayRef):
            k = 1
            G = []
            Y = binaryOp.right
            while k < self.n and isinstance(Y.name,pc.ArrayRef):
                G.append(Y.subscript)
                Y = Y.name
                k += 1
            if(Y.name == self.a):
                m = 0
                for g in G:
                    if(isinstance(g,pc.ID)):
                        self.depend[m] = self.depend[m] + [0]
                    elif(isinstance(g,pc.BinaryOp)):
                        if(isinstance(g.right,pc.ID) and isinstance(g.left,pc.Constant)):
                            if(g.op == "-"):
                                self.depend[m] = self.depend[m] +[-g.left.value]
                            elif(g.op == "+"):
                                self.depend[m] = self.depend[m] + [g.left.value]
                        if (isinstance(g.left, pc.ID) and isinstance(g.right, pc.Constant)):
                            if (g.op == "-"):
                                self.depend[m] = self.depend[m] + [-g.right.value]
                            elif (g.op == "+"):
                                self.depend[m] = self.depend[m] + [g.right.value]
                    elif(isinstance(g,pc.Constant)):
                        self.depend[m] = self.depend[m] + [0]
                    m += 1
        if isinstance(binaryOp.left, pc.ArrayRef):
            k = 0
            G = []
            Y = binaryOp.left
            while k < self.n and isinstance(Y.name, pc.ArrayRef):
                G.append(Y.subscript)
                Y = Y.name
                k += 1
            if (Y.name == self.a):
                m = 0
                for g in G:
                    if (isinstance(g, pc.ID)):
                        self.depend[m] = self.depend[m] + [0]
                    elif (isinstance(g, pc.BinaryOp)):
                        if (isinstance(g.right, pc.ID) and isinstance(g.left, pc.Constant)):
                            if (g.op == "-"):
                                self.depend[m] = self.depend[m] + [-g.left.value]
                            elif (g.op == "+"):
                                self.depend[m] = self.depend[m] + [g.left.value]
                        if (isinstance(g.left, pc.ID) and isinstance(g.right, pc.Constant)):
                            if (g.op == "-"):
                                self.depend[m] = self.depend[m] + [-g.right.value]
                            elif (g.op == "+"):
                                self.depend[m] = self.depend[m] + [g.right.value]
                    elif(isinstance(g,pc.Constant)):
                        self.depend[m] = self.depend[m] + [0]
                    m += 1


if __name__ == '__main__':
    ast = parse_file('./tests/c_files/p1_input7.c')
    l_f = TopLoopFinder()
    l_f.visit(ast)
    ast.show()
    print(l_f.__str__())