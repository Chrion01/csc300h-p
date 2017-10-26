import sys
from pycparser import parse_file
from pycparser.c_ast import *
from minic.minic_ast import *
class WhileVisitor(NodeVisitor):
    def __init__(self):
        self.nodes = []
    def visit_While(self, node):
        self.nodes.append(list(node.children()))
        node.show()

class ForVisitor(NodeVisitor):
    def __init__(self):
        self.nodes = []
    def visit_For(self, node):
        self.nodes.append(list(node.children()))
        node.show()

class ConstantVisitor(NodeVisitor):
    def __init__(self):
        self.values = []

    def visit_Constant(self, node):
        print('Const\n')
        self.values.append(node.value)

if __name__ == '__main__':
    ast = parse_file('./tests/c_files/minic.c')

    for_visit = ForVisitor()
    while_visit = WhileVisitor()
    n_vist = NodeVisitor()
    #n_vist.visit(ast)
    for_visit.visit(ast)
    while_visit.visit(ast)

    exit(0)