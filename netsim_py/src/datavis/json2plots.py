import logging
import ast
from models.nsdplot import PlotModel, DATA_TABLE, DerivedTable, Table,  Column, ColumnExpr, ColumnRef, Expression, \
    ConstantExpr, Operator, \
    AVG, COUNT, FIRST, LAST, MAX, MIN, SUM, \
    EQ, NOTEQ, LESS, LESS_EQ, GREATER, GREATER_EQ, \
    LAND, LOR, \
    PLUS, MINUS, DIV, MULT
from datavis.database import less_equal, less_than, greater_than, greater_equal, not_equal, like, not_like, between
from datavis.create_plot import pm_defaults
import json
import re


class ViewsPlotsDecoder:
    """
    Decodes views and plots in json format to DerivedTable and PlotModel respectively
    use the decode function
    """
    def __init__(self):
        self.derived_tables = []
        self.plot_models = []

    @staticmethod
    def xy_to_valid_col_tuple(xy, rel):
        """
        gets a x or y in the form of
        (node, n_index) or [node, n_index] or "node, n_index" (node, n_index are just example names)
        returns a tuple with objects of type Column according to names in xy
        """
        assert rel is not None
        if isinstance(xy, tuple) or xy is None:
            return tuple(rel.col[c] for c in xy)
        elif isinstance(xy, list):
            return tuple(rel.col[c] for c in xy)
        elif isinstance(xy, str):
            zoot = [c.strip() for c in xy.split(',')]
            return tuple(rel.col[c] for c in zoot)
        assert False  # What is this?

    @staticmethod
    def get_attr(attr, d, rel=None):
        """
        helper function to return the needed argument from dictionary d if it exists or get a default value for it
        rel is needed only for "x" and "y". It is the Table that columns in x and y belong
        """
        if attr in d and d[attr] != "":
            if attr in ["x", "y"]:
                xy = d[attr]
                if xy is None: return None
                return ViewsPlotsDecoder.xy_to_valid_col_tuple(xy, rel)
            else:
                return d[attr]
        elif attr in pm_defaults:
            return pm_defaults[attr]
        else:
            Exception("ViewsPlotsDecoder: Bad argument \"%s\"" % attr)

    @staticmethod
    def gen_plotmodel(rel, d):
        """
        generate a PlotModel associated to relation rel from specified dictionary d 
        (the dictionary should represent only one PlotModel)
        returns the PlotModel
        """
        sel = ViewsPlotsDecoder.get_attr("select", d)
        if sel != pm_defaults["select"]:
            if isinstance(sel, str):
                sdict = json.loads(sel)
                logging.root.debug("sdict = %s", sdict)
                sel = sdict
            sel = SelectorParser().parse(sel)

            logging.root.debug("d[x]= %s", d['x'])
            logging.root.debug("rel=%s", rel)

        pm = PlotModel(
            d["model_type"],
            d["stat_type"],
            rel,
            ViewsPlotsDecoder.get_attr("x", d, rel),
            ViewsPlotsDecoder.get_attr("y", d, rel),
            ViewsPlotsDecoder.get_attr("axes", d),
            sel,
            ViewsPlotsDecoder.get_attr("title", d),
            ViewsPlotsDecoder.get_attr("style", d),
            ViewsPlotsDecoder.get_attr("legend", d),
            ViewsPlotsDecoder.get_attr("xlabel", d),
            ViewsPlotsDecoder.get_attr("ylabel", d),
            ViewsPlotsDecoder.get_attr("x_range", d),
            ViewsPlotsDecoder.get_attr("y_range", d),
            ViewsPlotsDecoder.get_attr("logscale", d),
            ViewsPlotsDecoder.get_attr("grid", d),
            ViewsPlotsDecoder.get_attr("key", d),
            ViewsPlotsDecoder.get_attr("unit", d))
        return pm

    def gen_columns(self, d):
        """
        generate a list of Column objects from  d (d should be a list of dictionaries each representing a Column)
        returns the list of Column objects
        """
        cols = []
        for c in d:
            if "expression" in c and c["expression"] != "":
                expr = self.str_2_expr(c["expression"], gen_types(columns=cols))
                temp_c = ColumnExpr(c["name"], expr)
            else:
                temp_c = Column(c["name"])
            cols.append(temp_c)
        return cols

    def gen_plots(self, rel, d_plot_list):
        """
        generate PlotModels from d_plot_list which is a list of dictionaries representing the plots
        then add the generated PlotModels to plot_models (a list of PlotModels)
        rel is the relation these plots are connected with
        """
        for p in d_plot_list:
            pm = self.gen_plotmodel(rel, p)
            self.plot_models.append(pm)

    def gen_derived_table(self, d):
        """
        generate a DerivedTable from specified dictionary d (the dictionary should represent only one derived table)
        then add the generated DerivedTable to derived_tables (a list of DerivedTable)
        returns the DerivedTable
        """
        cols = self.gen_columns(d["columns"])
        base_tables = [self.get_table_by_name(name) for name in d["base_tables"]]
        if "groupby" in d and d["groupby"] not in ["", []]:
            groupby = col_str2col_obj(d["groupby"], cols)
        else:
            groupby = []

        dt = DerivedTable(
            d["name"],
            cols,
            base_tables,
            self.str_2_expr(d["table_filter"], gen_types(cols, base_tables)),
            groupby
        )
        self.derived_tables.append(dt)
        return dt

    def decode(self, views):
        """
        Decodes views and plots in json format to DerivedTable and PlotModel respectively
        returns a tuple of lists (list_DerivedTable, list_plotModel)
        """
        for v in views:
            if v["name"] == "dataTable":
                rel = DATA_TABLE
            else:
                rel = self.gen_derived_table(v)
            self.gen_plots(rel, v["plots"])

        return self.derived_tables, self.plot_models

    @staticmethod
    def str_2_expr(expr_str, types):
        """
        Parses the expression given in expr_str to an actual Expression object
        returns the generated Expression
        """
        nv = ExprGenNodeVisitor(types)
        eq_regex = re.compile(r"(?<![=><])=(?![=><])")  # regular expression to find a single =
        expr_str = eq_regex.sub("==", expr_str)  # replaces = with ==
        node = ast.parse(expr_str)
        return nv.visit(node)

    def get_table_by_name(self, name):
        """
        returns the Table with specified name
        """
        assert isinstance(name, str)

        if name == "dataTable":
            return DATA_TABLE
        else:
            for c in self.derived_tables:
                if c.name == name:
                    return c
        raise Exception("Table name: \"%s\" does not exist" % name)


def gen_types(columns=None, tables=None):
    """
    returns a dictionary containing all functions, columns and tables in the form:
    {
        "SUM": "function,
        "AVG": "funtion",
        "data": "column",
        "dataTable": "table"
        ....
        etc
    }
    functions are hardcoded, columns and table names are taken from arguments columns and tables
    """
    types = {
        "AVG": "function",
        "COUNT": "function",
        "FIRST": "function",
        "LAST": "function",
        "MAX": "function",
        "MIN": "function",
        "SUM": "function",
        "dataTable": "table"
    }

    if columns:
        for c in columns:
            types[c.name] = "column"
    if tables:
        for t in tables:
            types[t.name] = "table"
            for c in t.columns:
                types[c.name] = "column"

    return types


def get_col_by_name(name, cols):
    """
    returns the Column with specified name (cols is a list of columns where we search for name)
    None for not found
    """
    assert isinstance(name, str)
    assert isinstance(cols, list)

    for c in cols:
        if c.name == name:
            return c
    return None


def col_str2col_obj(col_str, col_obj):
    """
    returns a list of Column objects, defined by the list of column names
    col_str: the list of column names that we want to transform in Column objects
    col_obj: the list of all Column objects for one DerivedTable
    """
    assert isinstance(col_str, list)
    assert isinstance(col_obj, list)
    cols = []
    for s in col_str:
        c = get_col_by_name(s, col_obj)
        if c:
            cols.append(c)
        else:  # this should never happen
            raise Exception("column name: \"%s\" does not exist" % s)
    return cols


class ExprGenNodeVisitor(ast.NodeVisitor):
    def __init__(self, types):
        assert isinstance(types, dict)
        self.types = types

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
        func_name = self.visit(node.func)
        func = self.get_func_by_name(func_name)
        arg = self.visit(node.args[0])
        return Operator(func, [arg])

    def visit_Attribute(self, node):
        p = self.visit(node.value)
        col_name = node.attr
        c = Column(col_name, Table(p, []))
        c.table = Table(p, [])
        return ColumnRef(c)

    def visit_Name(self, node):
        name = str(node.id)
        if name in self.types:
            if self.types[name] == "function":
                return name
            elif self.types[name] == "column":
                return ColumnRef(Column(name))
            elif self.types[name] == "table":
                return name
        else:
            raise Exception("Unknown Name: \"%s\"" % name)

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


class SelectorParser():
    """
    Parses a dictionary to a Selector, use function parse
    dictionary format:
    select={'theta':less_than(0.125)&greater_than(0.115), 'servers':between(3,6)}
    """
    allowed_funcs = {
        "less_equal": less_equal,
        "less_than": less_than,
        "greater_than": greater_than,
        "greater_equal": greater_equal,
        "not_equal": not_equal,
        "like": like,
        "not_like": not_like,
        "between": between
    }

    def parse(self, selector_dict):
        logging.root.debug("Selector is %s", selector_dict)
        logging.root.debug("Selector is %s", type(selector_dict))
        assert isinstance(selector_dict, dict)
        for attr in selector_dict:
            sel_str = selector_dict[attr]
            selector_dict[attr] = eval(sel_str, self.allowed_funcs)
        return selector_dict

