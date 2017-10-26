from pycparser import c_ast
import minic_ast as mc


# Assignments are all converted into assignments using the '=' operator.
# All assignments using other operators are converted into assignments
# using the '=' and the expression on the right hand side is a binary
# expression such that the assignment has the same semantics.
def of_assignment(orig):
    lvalue = t(orig.lvalue)
    if orig.rvalue is not None:
        rvalue = t(orig.rvalue)
    else:
        rvalue = None

    final_rvalue = {
        '=': rvalue,
        '+=': mc.BinaryOp('+', lvalue, rvalue),
        '-=': mc.BinaryOp('-', lvalue, rvalue),
        '*=': mc.BinaryOp('*', lvalue, rvalue),
        '/=': mc.BinaryOp('/', lvalue, rvalue),
        '%=': mc.BinaryOp('%', lvalue, rvalue),
        '^=': mc.BinaryOp('^', lvalue, rvalue),
        '|=': mc.BinaryOp('|', lvalue, rvalue),
        '>>=': mc.BinaryOp('>>', lvalue, rvalue),
        '<<=': mc.BinaryOp('<<', lvalue, rvalue),
        '&=': mc.BinaryOp('&', lvalue, rvalue),
        '++': mc.BinaryOp('+', lvalue, mc.Constant('int', '1')),
        '--': mc.BinaryOp('-', lvalue, mc.Constant('int', '1')),
    }.get(orig.op, mc.EmptyStatement())

    return mc.Assignment(lvalue, final_rvalue, coord=orig.coord)


# PyCParser represents increment and decrement as unary operations, we convert them
# to assignments. Other unary operators are kept as is.
def maybe_special_unary(orig):
    return {
        'p--': (lambda x: mc.Assignment(x, mc.BinaryOp('-', x, mc.Constant('int', '1')))),
        'p++': (lambda x: mc.Assignment(x, mc.BinaryOp('+', x, mc.Constant('int', '1')))),
        '--': (lambda x: mc.Assignment(x, mc.BinaryOp('-', x, mc.Constant('int', '1')))),
        '++': (lambda x: mc.Assignment(x, mc.BinaryOp('+', x, mc.Constant('int', '1'))))
    }.get(orig.op, lambda x: mc.UnaryOp(orig.op, x))(t(orig.expr))


# If there is no match case in the dictionary style switch, then it means it is a construct
# that is not supported in minic.
def nomatch(y):
    if y is None:
        return None
    else:
        print ("No match found for class %r" % y.__class__)
        y.show()
        raise TypeError


# Checks that the original construct is a value, a not any another construct. It helps
# in checking that we have terminal symbols at the right places.
def v(orig):
    if isinstance(orig, str) or isinstance(orig, int) or isinstance(orig, float) \
            or isinstance(orig, bool) or orig is None:
        return orig
    else:
        print ("Unexpected type for value %r" % orig)
        raise TypeError


def tmap(x):
    if isinstance(x, list):
        map(t, x)
    else:
        t(x)


# The main transformer function. This is close to a mapping for PyCparser AST nodes to Minic nodes, except
# that there are less constructs and we have to transform assignments and unary operators.
def t(x):
    return {
        c_ast.ArrayDecl: (lambda orig: mc.ArrayDecl(t(orig.type), orig.dim, coord=orig.coord)),
        c_ast.ArrayRef: (lambda orig: mc.ArrayRef(t(orig.name), t(orig.subscript))),
        c_ast.Assignment: (lambda orig: of_assignment(orig)),
        c_ast.BinaryOp: (lambda orig: mc.BinaryOp(v(orig.op), t(orig.left), t(orig.right), coord=orig.coord)),
        c_ast.Compound: (lambda orig: mc.Block(map(t, orig.block_items), coord=orig.coord)),
        c_ast.Constant: (lambda orig: mc.Constant(t(orig.type), v(orig.value), coord=orig.coord)),
        c_ast.Decl: (lambda orig: mc.Decl(t(orig.name), t(orig.funcspec), t(orig.type), t(orig.init), coord=orig.coord)),
        c_ast.DeclList: (lambda orig: mc.DeclList(tmap(orig.decls), coord=orig.coord)),
        c_ast.DoWhile: (lambda orig: mc.DoWhile(t(orig.cond), t(orig.stmt), coord=orig.coord)),
        c_ast.EmptyStatement: (lambda orig: mc.EmptyStatement()),
        c_ast.ExprList: (lambda orig: mc.ExprList(tmap(orig.exprs))),
        c_ast.FileAST: (lambda orig: mc.FileAST(map(t, orig.ext))),
        c_ast.For: (lambda orig: mc.For(t(orig.init), t(orig.cond), t(orig.next), t(orig.stmt), coord=orig.coord)),
        c_ast.FuncCall: (lambda orig: mc.FuncCall(t(orig.name), tmap(orig.args))),
        c_ast.FuncDecl: (lambda orig: mc.FuncDecl(tmap(orig.args), t(orig.type))),
        c_ast.FuncDef: (lambda orig: mc.FuncDef(t(orig.decl), tmap(orig.param_decls), t(orig.body))),
        c_ast.ID: (lambda orig: mc.ID(v(orig.name))),
        c_ast.IdentifierType: (lambda orig: mc.IdentifierType(tmap(orig.names))),
        c_ast.If: (lambda orig: mc.If(t(orig.cond), t(orig.iftrue), t(orig.iffalse))),
        c_ast.InitList: (lambda orig: mc.InitList(tmap(orig.exprs))),
        c_ast.NamedInitializer: (lambda orig: mc.NamedInitializer(v(orig.name), t(orig.expr))),
        c_ast.ParamList: (lambda orig: mc.ParamList(tmap(orig.params))),
        c_ast.PtrDecl: (lambda orig: mc.PtrDecl(t(orig.type))),
        c_ast.Return: (lambda orig: mc.Return(t(orig.expr))),
        c_ast.TernaryOp: (lambda orig: mc.TernaryOp(t(orig.cond), t(orig.iftrue), t(orig.iffalse))),
        c_ast.Typename: (lambda orig: mc.Typename(v(orig.name), t(orig.type))),
        c_ast.TypeDecl: (lambda orig: mc.TypeDecl(v(orig.declname), t(orig.type))),
        c_ast.UnaryOp: (lambda orig: maybe_special_unary(orig)),
        c_ast.While: (lambda orig: mc.While(t(orig.cond), t(orig.stmt))),
        str: (lambda orig: orig),
        int: (lambda orig: orig),
        float: (lambda orig: orig),
        list: (lambda orig: tmap(orig))
    }.get(x.__class__, lambda y: nomatch(y))(x)
