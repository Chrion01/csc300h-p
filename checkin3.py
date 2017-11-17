import sys
from pycparser import parse_file
import pycparser.c_ast as pc
from minic.minic_ast import *
from minic.c_ast_to_minic import *


class Top_Loop_Finder(NodeVisitor):

    def __init__(self):
        self.nodes = []
        self.nested = {}

    def visit_For(self, For):
        self.nodes.append(For)
        f_vis = LoopVisitor()
        f_vis.visit(For)
        print(f_vis.index_vector)
        if len(f_vis.index_vector) > 1:
            self.nested[For] = [f_vis.index_vector]


    def __str__(self):
        res = ""
        for node in self.nested.keys():
            res += 'Loop nest: {}\n'.format(node)
            res += '\tIndex Vector: {}'.format(self.nested[node])
        return res

class LoopVisitor(NodeVisitor):

    def __init__(self):
        self.nodes = []
        self.index_vector = []

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
            self.index_vector += (f_vis.index_vector)

if __name__ == '__main__':
    ast = parse_file('./tests/c_files/p1_input6.c')
    l_f = Top_Loop_Finder()
    l_f.visit(ast)
    print(l_f.__str__())