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
            index = init
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
        self.left_side_temp = self.left_side_temp = [0] * len(self.index_vector)
        self.writes = []
        self.reads = {}

    def visit_Assignment(self, Assign):
        self.temp_holder = []
        self.left_side_temp = self.left_side_temp = [0] * len(self.index_vector)
        if isinstance(Assign.lvalue, pc.ArrayRef):
            l = self.array_index_converter(Assign.lvalue)
            # if l[0] not in self.writes.keys():
            #     self.writes[l[0]] = []
            #     self.writes[l[0]].append(l[1].copy())
            # else:
            #     self.writes[l[0]].append(l[1].copy())
            self.writes.append(l)
            self.temp_holder = []

        self.visit(Assign.rvalue)

        if self.temp_holder:
            self.dependencies[transform(Assign).__str__()] = []
            for res in self.temp_holder:
                self.dependencies[transform(Assign).__str__()].append(self.dep_vector_cal(l, res))

    def visit_ArrayRef(self, aRef):
        assert(isinstance(aRef, pc.ArrayRef))
        # if isinstance(aRef.subscript, pc.Constant):
        #     return None
        l = self.array_index_converter(aRef)
        if l[0] not in self.reads.keys():
            self.reads[l[0]] = []
            self.reads[l[0]].append(l[1].copy())

        else:
            self.reads[l[0]].append(l[1].copy())

        # if isinstance(aRef.subscript, pc.ID):
        #     res = self.writer(aRef.subscript.name, 0, 0)
        #     if res is not None:
        #         self.temp_holder.append(res.copy())
        #         # return res.copy()
        # elif isinstance(aRef.subscript, pc.BinaryOp):
        #     handle = self.subscript_handler(aRef.subscript)
        #     if handle is not None:
        #         res = self.writer(handle[0], handle[1], handle[2])
        #         if res is not None:
        #             self.temp_holder.append(res.copy())
        #             # return res.copy()
        self.temp_holder.append(l)
        return

    def array_index_converter(self, arrayRef):
        # returns array refs in format (name, [subscripts])
        name = ''
        subsc = []
        if isinstance(arrayRef.name, pc.ArrayRef):
            nest = self.array_index_converter(arrayRef.name)
            name = nest[0]
            subsc = nest[1]

        elif isinstance(arrayRef.name, pc.ID):
            name = arrayRef.name.name
        subsc.append(self.subscript_handler(arrayRef.subscript).copy())

        return (name, subsc)


    def subscript_handler(self, subscript):
        # gets operation and value from array subscripts
        # returns (variable name, operator, constant) or None if not in x + 1 or 1 - x format.
        if isinstance(subscript, pc.ID):
            return [subscript.name, '+', 0]
        elif isinstance(subscript, pc.BinaryOp):
            if isinstance(subscript.left, pc.ID):
                return [subscript.left.name, subscript.op, int(subscript.right.value)]
            elif isinstance(subscript.right, pc.ID):
                return [subscript.right.name, subscript.op, int(subscript.left.value)]
        else:
            return None

    def dep_vector_cal(self, left, right):
        # input assignment lvalue in array index converter format
        #                   rvalue in array index converter format
        # returns dependency vector of left to right

        num = len(self.index_vector)
        left_vector = [0] * num
        for i in left[1]:
            x = 0
            for var in self.index_vector:
                if var == i[0]:
                    if i[1] == '-':
                        left_vector[x] = -1 * i[2]
                    else:
                        left_vector[x] = i[2]
                x += 1
        right_vector = [0] * num
        for i in right[1]:
            x = 0
            for var in self.index_vector:
                if var == i[0]:
                    if i[1] == '-':
                        right_vector[x] = -1 * i[2]
                    else:
                        right_vector[x] = i[2]
                x += 1
        dep_vector = []
        for i in range(num):
            dep_vector.append(left_vector[i]-right_vector[i])

        # lex. pos. check
        self.lexicographically_positive(dep_vector)

        # incase of past.
        in_past = False
        for i in range(1, num):
            if dep_vector[i - 1] > 0:
                in_past = True
                break
            if (not in_past) and dep_vector[i] < 0 and dep_vector[i - 1] == 0:
                dep_vector[i - 1] += 1
                break
        return dep_vector

    def lexicographically_positive(self, vector):
        positive = True
        first_neg = False
        if vector[0] < 0:
            return False
        for x in vector:
            if x < 0 and not first_neg:
                first_neg = True
            elif x >= 0 and first_neg:
                positive = False
                break
        return positive

    # DEPRECATED BY dep_vector_cal
    #
    # def writer(self, id, operation, dist):
    #     index = 0
    #     for var in self.index_vector:
    #         if var == id:
    #             break
    #         index += 1
    #     if index >= len(self.index_vector):
    #         return None
    #     dep = []
    #     try:
    #         dist_int = int(dist)
    #     except ValueError:
    #         dist_int = None
    #     if dist_int:
    #         dist = dist_int
    #     for i in range(len(self.index_vector)):
    #         if i == index - 1:
    #             if operation == '+':
    #                 dep.append(-1 * dist - self.left_side_temp[i])
    #             else:
    #                 dep.append(0 - self.left_side_temp[i])
    #         elif i == index:
    #             if operation == '+':
    #                 dep.append(-1 * dist - self.left_side_temp[i])
    #             elif operation == '-':
    #                 dep.append(dist - self.left_side_temp[i])
    #             else:
    #                 dep.append(0 - self.left_side_temp[i])
    #         else:
    #             dep.append(0 - self.left_side_temp[i])
    #
    #     # lex. pos. check
    #     pos = True
    #     first_neg = False
    #     for x in dep:
    #         if x < 0 and not first_neg:
    #             first_neg = True
    #         elif x >= 0 and first_neg:
    #             pos = False
    #             break
    #     return dep



if __name__ == '__main__':
    ast = parse_file('./tests/c_files/checkin4_ex.c')
    l_f = TopLoopFinder()
    l_f.visit(ast)
    ast.show()
    print(l_f.__str__())