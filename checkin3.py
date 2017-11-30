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
            dv.out_dep_calc()
            self.nested[For].append(dv.anti_deps)
            self.nested[For].append(dv.out_deps)

    def __str__(self):
        res = ""
        for node in self.nested.keys():
            res += 'Loop nest: {}\n'.format(node)
            res += '\tIndex Vector: {}\n'.format(self.nested[node][0])
            res += '\tDependence vectors:\n'
            deps = self.nested[node][1].keys()
            for dep in deps:
                res += '\t\tStatement {} : D = {}\n'.format(dep, self.nested[node][1][dep])
            anti_deps = self.nested[node][2]
            res += '\tAnti Dependences:\n'
            for ad in anti_deps:
                res += '\t\t{}\n'.format(ad)
            out_deps = self.nested[node][3]
            res += '\tOutward Dependences:\n'
            for od in out_deps:
                res += '\t\t{}\n'.format(od)

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
        self.writes = []
        self.reads = {}
        self.anti_deps = []
        self.out_deps = []

    def visit_Assignment(self, Assign):
        self.temp_holder = []


        self.visit(Assign.rvalue)

        if isinstance(Assign.lvalue, pc.ArrayRef):
            l = self.array_index_converter(Assign.lvalue)
            # if l[0] not in self.writes.keys():
            #     self.writes[l[0]] = []
            #     self.writes[l[0]].append(l[1].copy())
            # else:
            #     self.writes[l[0]].append(l[1].copy())
            self.writes.append(l)
        else:
            l = None
        if self.temp_holder and l:
            self.dependencies[transform(Assign).__str__()] = []
            for res in self.temp_holder:
                self.dependencies[transform(Assign).__str__()].append(self.dep_vector_cal(l, res))
        self.anti_dep_calc()

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
        """Converts ArrayRef into usable format

        :param arrayRef: ArrayRef
        :return [str, list, str]: list of array name, list of its indexes in subscript_handler format. Indexes in order
                                    and a string representation of the original arrayRef
        """
        # returns array refs in format (name, [subscripts])
        name = ''
        subsc = []
        if isinstance(arrayRef.name, pc.ArrayRef):
            nest = self.array_index_converter(arrayRef.name)
            name = nest[0]
            subsc = nest[1]

        elif isinstance(arrayRef.name, pc.ID):
            name = arrayRef.name.name
        try:
            subsc.append(self.subscript_handler(arrayRef.subscript).copy())
            transform(arrayRef).__str__()

            return [name, subsc, transform(arrayRef).__str__()]
        except AttributeError:
            print('Conversion failed for {}'.format(transform(arrayRef).__str__()))
            return [name, [], transform(arrayRef).__str__()]

    @staticmethod
    def subscript_handler(subscript):
        """Returns formated version of arrayRef subscripts

        Assumes subscript is in [ID +/- integer], [integer +/- ID], or [ID] format
        :param subscript: ArrayRef.subscript
        :return list[str, str, int]: [variable name, binary operation, |offset from 0|]
        """
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
        """ Calculates dependency vector

        Uses class index_vector to determine ordering of array indexes

        :param left: ArrayRef on lefthand side of assignment statement in array_index_converter format
        :param right: ArrayRef on righthand side of assignment statement in array_index_converter format
        :return list of int: Dependency vector of right to left
        """

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
        positive, position = self.lexicographically_positive(dep_vector)
        if positive and position != -1:
            if dep_vector[position] == 0:
                dep_vector[position] += 1

        return dep_vector

    @staticmethod
    def lexicographically_positive(vector):
        """Determine lexicographical positivity and returns position of last value

        Returns position of last value >= 0 prior to the first negative value
        - If not lex. pos. returns False, 0
        - If there are no negative values, returns True, -1
        :param vector: Vector should be greater than length 1
        :return boolean, int:
        """

        if vector[0] < 0:
            return False, 0
        for x in range(1, len(vector)):
            if vector[x] < 0:
                return True, x - 1
        return True, -1

    def anti_dep_calc(self):
        for ref in self.temp_holder:
            for comp in self.writes:
                if ref[0] == comp[0]:
                    if self.bef_aft(comp, ref) == 1:
                        self.anti_deps.append([comp[2], ref[2]])

        return

    def out_dep_calc(self):
        for ref in range(len(self.writes)):
            for comp in range(ref + 1, len(self.writes)):
                if self.writes[ref][0] == self.writes[comp][0]:
                    if self.bef_aft(self.writes[ref], self.writes[comp]) == -1:
                        self.out_deps.append([self.writes[ref][2], self.writes[comp][2]])

        return

    @staticmethod
    def bef_aft(first, second):
        """

        :param first:  ArrayRef to be compared against in array_index_converter format
        :param second: ArrayRef to compare to first in array_index_converter format
        :return int: -1 if the second is a later iteration, 1 if prior iteration, 0 if same
        """
        assert(first[0] == second[0])
        left = first[1]
        right = second[1]
        for i in range(len(left)):
            if left[i] > right[i]:
                return 1
            elif left[i] < right[i]:
                return -1

        return 0

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
    ast = parse_file('./tests/c_files/p1_input8.c')
    l_f = TopLoopFinder()
    l_f.visit(ast)
    # ast.show()
    print(l_f.__str__())