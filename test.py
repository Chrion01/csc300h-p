import main
from pycparser import parse_file



if __name__ == '__main__':
    path = './tests/c_files/p1_input'
    files = ['1.c', '2.c', '3.c','4.c','5.c', '6.c', '7.c', '8.c']
    for file in files:
        full = path + file
        print('Test file: {}'.format(full))
        ast = parse_file(full)

        fv = main.FuncVisitor()
        fv.visit(ast)
        for loop in fv.loops:
            print(loop)


