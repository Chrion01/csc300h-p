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
            dv = DependenceCalc(f_vis.index_vector)
            dv.visit(For)
            self.nested[For].append(dv.dependencies)

    def __str__(self):
        res = ""
        for node in self.nested.keys():
            res += 'Loop nest: {}\n'.format(node)
            res += '\tIndex Vector: {}\n'.format(self.nested[node][0])
            res += '\tDependence vectors:\n'
            deps = self.nested[node][1].keys()
            for dep in deps:
                res += '\t\tStatement {} : D = {}\n'.format(dep, self.nested[node][1][dep])
        return res



class LoopVisitor(NodeVisitor):

    def __init__(self):
        self.nodes = []
        self.index_vector = []
        self.dependencyVector = {}


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

    def __init__(self, index_vector):
        self.dependencies = {}
        self.index_vector = index_vector
        self.temp_holder = []

    def visit_Assignment(self, Assign):
        self.temp_holder = []
        self.visit(Assign.rvalue)
        if self.temp_holder:
            self.dependencies[transform(Assign).__str__()] = self.temp_holder.copy()

    def visit_ArrayRef(self, aRef):
        assert(isinstance(aRef, pc.ArrayRef))
        # if isinstance(aRef.subscript, pc.Constant):
        #     return None
        if isinstance(aRef.name, pc.ArrayRef):
            self.visit(aRef.name)
        if isinstance(aRef.subscript, pc.ID):
            res = self.writer(aRef.subscript.name, 0, 0)
            if res is not None:
                self.temp_holder.append(res.copy())
                # return res.copy()
        elif isinstance(aRef.subscript, pc.BinaryOp):
            handle = self.subscriptBinaryHandler(aRef.subscript)
            if handle is not None:
                res = self.writer(handle[0], handle[1], handle[2])
                if res is not None:
                    self.temp_holder.append(res.copy())
                    # return res.copy()

        # return None

    def subscriptBinaryHandler(self, binOp):
        assert (isinstance(binOp, pc.BinaryOp))

        if isinstance(binOp.left, pc.ID):
            return [binOp.left.name, binOp.op, binOp.right.value]
        elif isinstance(binOp.right, pc.ID):
            return [binOp.right.name, binOp.op, binOp.left.value]
        else:
            return None

    def writer(self, id, operation, dist):
        index = 0
        for var in self.index_vector:
            if var == id:
                break
            index += 1
        if index >= len(self.index_vector):
            return None
        dep = []
        try:
            dist_int = int(dist)
        except ValueError:
            dist_int = None
        if dist_int:
            dist = dist_int
        for i in range(len(self.index_vector)):
            if i == index - 1:
                if operation == '+':
                    dep.append(-1 * dist)
                else:
                    dep.append(0)
            elif i == index:
                if operation == '+':
                    dep.append(-1 * dist)
                elif operation == '-':
                    dep.append(dist)
                else:
                    dep.append(0)
            else:
                dep.append(0)
        return dep


if __name__ == '__main__':
    ast = parse_file('./tests/c_files/p1_input7.c')
    l_f = TopLoopFinder()
    l_f.visit(ast)
    ast.show()
    print(l_f.__str__())