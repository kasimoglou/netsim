import ast
from models.nsdplot import PlotModel, DATA_TABLE, DerivedTable, Table,  Column, ColumnExpr, ColumnRef, \
    ConstantExpr, Operator, \
    AVG, COUNT, FIRST, LAST, MAX, MIN, SUM, \
    EQ, NOTEQ, LESS, LESS_EQ, GREATER, GREATER_EQ, \
    LAND, LOR, \
    PLUS, MINUS, DIV, MULT
import re


def gen_plotmodel(rel, d):
    """
    generate a PlotModel associated to relation rel from specified dictionary d (the dictionary should represent only one PlotModel)
    returns the PlotModel
    """
    pm = PlotModel(
        d["model_type"],
        d["stat_type"],
        rel,
        tuple([rel.col[x] for x in d["x"]]),
        tuple([rel.col[y] for y in d["y"]]),
        d["axes"],
        None,  # TODO: parsing
        d["title"],
        d["style"],
        d["legend"],
        d["xlabel"],
        d["ylabel"],
        d["x_range"],
        d["y_range"],
        d["logscale"],
        d["grid"],
        d["key"],
        d["unit"])
    return pm


def gen_columns(d):
    """
    generate a list of Column objects from  d (d should be a list of dictionaries each representing a Column)
    returns the list of Column objects
    """
    cols = []
    for c in d:
        expr = str_2_expr(c["expression"])
        temp_c = ColumnExpr(c["name"], expr)
        cols.append(temp_c)
    return cols


def get_col_by_name(name, cols):
    """
    returns the Column with specified name (cols is a list of columns)
    None for not found
    """
    assert isinstance(name, str)
    assert isinstance(cols, list)

    for c in cols:
        if c.name == name:
            return c
    return None


def col_str_2_col_obj(col_str, col_obj):
    """
    returns a list of Column objects, defined by the list of column names
    col_str: the list of column names that we want to transform in Column objects
    col_obj: the list of all Column objects for one DerivedTable
    """
    cols = []
    for s in col_str:
        c = get_col_by_name(s, col_obj)
        if c:
            cols.append(c)
        else:  # this should never happen
            raise Exception("column name: \"%s\" does not exist" % s)
    return cols


def gen_derived_table(d):
    """
    generate a DerivedTable from specified dictionary d (the dictionary should represent only one derived table)
    returns the DerivedTable
    """
    cols = gen_columns(d["columns"])
    dt = DerivedTable(
        d["name"],
        cols,
        d["base_tables"],  # keep this as list of strings for now, later translate to DerivedTable
        str_2_expr(d["table_filter"]),
        col_str_2_col_obj(d["groupby"], cols)
    )
    return dt


def get_table_by_name(name, tables):
    """
    returns the Table with specified name (tables is a list of Tables/DerivedTables)
    None for not found
    """
    assert isinstance(name, str)
    assert isinstance(tables, list)

    for c in tables:
        if c.name == name:
            return c
    return None


def table_str_2_table_obj(table_str, table_obj):
    """
    returns a list of Table/DerivedTable objects, defined by the list of Table names
    btable_str: the list of Table names that we want to transform in Table/DerivedTable objects
    btable_obj: the list of all Table/DerivedTable objects
    """
    tables = []
    for s in table_str:
        if s == "dataTable":
            t = DATA_TABLE
        else:
            t = get_table_by_name(s, table_obj)

        if t:
            tables.append(t)
        else:  # this should never happen
            raise Exception("Table name: \"%s\" does not exist" % s)
    return tables


def gen_add_plots(rel, d_plot_list, plot_models):
    """
    generate PlotModels from d_plot_list which is a list of dictionaries representing the plots
    then add the generated PlotModels to plot_models (a list of PlotModels)
    rel is the relation these plots are connected with
    """
    for p in d_plot_list:
        pm = gen_plotmodel(rel, p)
        plot_models.append(pm)


def views_plots_decoder(views):
    """
    Decodes views and plots in json format to DerivedTable and PlotModel respectively
    returns a tuple of lists (list_DerivedTalbe, list_plotModel)
    """
    derived_tables = []
    plot_models = []
    for v in views:
        if v["name"] == "dataTable":
            rel = DATA_TABLE
            gen_add_plots(rel, v["plots"], plot_models)
        else:
            dt = gen_derived_table(v)
            derived_tables.append(dt)
            rel = dt
            gen_add_plots(rel, v["plots"], plot_models)

    for dt in derived_tables:
        dt.base_tables = table_str_2_table_obj(dt.base_tables, derived_tables)

    return derived_tables, plot_models


class ExprGenNodeVisitor(ast.NodeVisitor):

    def visit_Module(self, node):
        return self.visit(node.body[0])

    def visit_Expr(self, node):
        return self.visit(node.value)

    def visit_BinOp(self, node):
        a = self.visit(node.left)
        op_name = type(node.op).__name__
        op = self.get_func_by_name(op_name)
        b = self.visit(node.right)
        return Operator(op, [a, b])

    def visit_BoolOp(self, node):
        op_name = type(node.op).__name__
        op = self.get_func_by_name(op_name)
        return Operator(op, list(map(lambda x: self.visit(x), node.values)))

    def visit_Compare(self, node):
        a = self.visit(node.left)
        op_name = type(node.ops[0]).__name__
        op = self.get_func_by_name(op_name)
        b = self.visit(node.comparators[0])
        return Operator(op, [a, b])

    def visit_Call(self, node):
        func_name = self.visit(node.func).column.name
        func = self.get_func_by_name(func_name)
        arg = self.visit(node.args[0])
        return Operator(func, [arg])

    def visit_Attribute(self, node):
        p = self.visit(node.value).column.name
        col_name = node.attr
        c = Column(col_name, Table(p, []))
        c.table = Table(p, [])
        return ColumnRef(c)

    def visit_Name(self, node):
        name = str(node.id)
        return ColumnRef(Column(name))

    def visit_Num(self, node):
        num = str(node.n)
        return ConstantExpr(num)

    def visit_Str(self, node):
        s = str(node.s)
        return ConstantExpr(s)

    @staticmethod
    def get_func_by_name(name):
        funcs = [AVG, COUNT, FIRST, LAST, MAX, MIN, SUM, LAND, LOR]
        for f in funcs:
            if name.lower() == f.name.lower():
                return f
        if name == "Eq":
            return EQ
        elif name == "NotEq":
            return NOTEQ
        elif name == "Lt":
            return LESS
        elif name == "LtE":
            return LESS_EQ
        elif name == "Gt":
            return GREATER
        elif name == "GtE":
            return GREATER_EQ
        elif name == "Add":
            return PLUS
        elif name == "Sub":
            return MINUS
        elif name == "Mult":
            return MULT
        elif name == "Div":
            return DIV

        raise Exception("func \"%s\" unknown" % name)


def str_2_expr(expr_str):
    """
    Parses the expression given in expr_str to an actual Expression object
    returns the generated Expression
    """
    nv = ExprGenNodeVisitor()
    eq_regex = re.compile(r"(?<![=><])=(?![=><])")  # regular expression to find a single =
    expr_str = eq_regex.sub("==", expr_str)  # replaces = with ==
    node = ast.parse(expr_str)
    return nv.visit(node)