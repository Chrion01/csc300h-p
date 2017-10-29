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
class LoopVisitor(NodeVisitor):
    def __init__(self):
        self.nodes = []
    def visit_For(self, For):
        self.nodes.append(list(For.children()))
        b_vist = BodyVisitor()
        b_vist.visit(For)

    def visit_While(self, While):
        self.nodes.append(list(While.children()))
        b_vist = BodyVisitor()
        b_vist.visit(While)

class BodyVisitor(NodeVisitor):
    def __init__(self):
        self.values = []

    def visit_Assignment(self, assignment):
        self.values.append(assignment.lvalue.name)
        assignment.lvalue.show()
    def visit_Decl(self, decl):
        self.values.append(decl.name)

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
    n_vist = LoopVisitor()
    n_vist.visit(ast)



    exit(0)