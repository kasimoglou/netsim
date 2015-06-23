from models.mf import model, attr, ref, ref_list



##############################
#  Statistics: part of an NSD
##############################


@model
class Column:
    """
    Describes a column in a table
    table with all available columns:
    _________________________________________________
    | module | node | name | label | n_index | data |
    |        |      |      |       |         |      |
    |        |      |      |       |         |      |

    """

    def __init__(self, name, parent=None):
        self.name = name
        self.parent = parent

    # the column name
    name = attr(str)

    # the table this column will be derived from when creating views
    # this is needed if the same column appears in two tables that are used to create a view
    # and the column will be present in the view
    parent = attr(object)  # TODO: should be Table but generates errors

    # the table this column belongs to
    table = ref()


@model
class Table:
    """
    Describes a table with columns
    """

    def __init__(self, name, columns=[], filename=None, format=None, node_mapping=None):
        self.name = name
        self.columns = columns
        # just for easy access to columns by name
        #self.col = {self.columns[i].name: self.columns[i] for i in list(range(len(self.columns)))}
        self.col = {col.name:col for col in self.columns}
        self.filename = filename
        self.format = format
        self.node_mapping = node_mapping

    # the name for this table
    name = attr(str, nullable=False)

    # the columns contained in this table
    columns = ref_list(inv=Column.table)


@model
class Function:
    def __init__(self, name, isinline, isaggregate=False):
        self.name = name
        self.isinline = isinline
        self.isaggregate = isaggregate

    # name of function
    name = attr(str, nullable=False)
    isinline = attr(bool, nullable=False)
    isaggregate = attr(bool, nullable=False)


PLUS = Function('+', True)
MINUS = Function('-', True)
DIV = Function('/', True)
MULT = Function('*', True)

EQ = Function('=', True)
NOTEQ = Function('<>', True)

LESS = Function('<', True)
LESS_EQ = Function('<=', True)

GREATER = Function('>', True)
GREATER_EQ = Function('>=', True)

AVG = Function('AVG', False, True)
COUNT = Function('COUNT', False, True)
MAX = Function('MAX', False, True)
MIN = Function('MIN', False, True)
SUM = Function('SUM', False, True)

LAND = Function('AND', True)
LOR = Function('OR', True)


@model
class Expression:
    parent = ref()


@model
class Operator(Expression):
    def __init__(self, function, operands):
        self.function = function
        self.operands = operands
    function = attr(Function)
    operands = ref_list(inv=Expression.parent)


@model
class ColumnExpr(Column):
    """
    A column in a derived table, defined by an expression.
    """
    def __init__(self, name, expression, alias=None):
        super().__init__(name)
        self.expr = expression
        if alias:
            self.alias = alias
        else:
            self.alias = name

    # the expression defining the column of a derived table
    expr = attr(Expression)
    # the alias for this column
    alias = attr(str)


@model
class ConstantExpr(Expression):
    def __init__(self, val=None):
        self.value = val
    
    value = attr(type=object)

@model
class ColumnRef(Expression):
    """An expression referencing a column."""
    def __init__(self, column):
        self.column = column
    column = attr(Column)


@model
class DerivedTable(Table):
    """
    Describes a table that derives from one or more other tables
    """

    def __init__(self, name, columns, base_tables, table_filter, groupby=None):
        super().__init__(name, columns)
        self.base_tables = base_tables
        self.table_filter = table_filter
        self.groupby = groupby

    #the tables from which this one derived
    base_tables = attr(list) 

    #the table's filter, decides which columns/values will be left in this derived table
    table_filter = attr(Expression)

    # group-by columns
    groupby = attr(list)


@model
class DataTable(Table):
    """
    Deprecated
    The table that will hold all information generated from the simulation
    ============ ONLY USED DURING TESTS ============
    """
    def __init__(self):
        super().__init__('dataTable', [Column("module"),
                                       Column("node"),
                                       Column("name"),
                                       Column("label"),
                                       Column("n_index"),
                                       Column("data"),
                                       ], "simout.txt", "dataTable", ["node", "n_index"])


# Deprecated (used only during tests)
DATA_TABLE = DataTable()


@model 
class PlotModel:
    """
    Describes a plot or parameter (statistic) to be generated after the simulation finishes
    """
    model_type = attr(str)    # can be "plot", "parameter"
    stat_type = attr(str)     # can be "node", "network", "node2node"

    #
    # applicable only to model_type "parameter"
    #
    unit = attr(str)          # the statistic's unit eg. seconds

    #
    # applicable to both model types
    #
    rel = attr(Table)
    x = attr(tuple)
    y = attr(tuple)
    select = attr(object)  # To be elaborated into name-predicate pair (predicate is either value, list of values or Selector)
    title = attr(str, default='DEFAULT')

    #
    # applicable only to model_type "plot"
    #
    axes = attr(list)  # TODO: applicable to both ?
    style = attr(str, default='linespoints')   # e.g., 'linespoints',
    legend = attr(str, default='DEFAULT')  # DEFAULT,
    xlabel = attr(str)    # gnuplot syntax
    ylabel = attr(str)    # gnuplot syntax
    x_range = attr(str)   # gnuplot syntax
    y_range = attr(str)   # gnuplot syntax
    logscale = attr(str)  # gnuplot syntax
    grid = attr(str)      # gnuplot syntax
    key = attr(str)       # gnuplot syntax

    # These two are hard-coded (!)
    #terminal = None
    #output = DEFAULT
    def __init__(self, model_type, stat_type, rel, x, y, axes=None, select={}, title='DEFAULT', style='linespoints',
              legend='DEFAULT', xlabel=None, ylabel=None, x_range=None, y_range=None, logscale=None, grid=" ",
              key=None, unit=""):
        """
        Return a Plot object, containing a number of Graph objects.

        The graphs contained in the plot are produced as follows:
        First, the following query (in pseudo-SQL) is executed
        SELECT DISTINCT axes... FROM rel WHERE select... ORDER BY axes...

        For each result row R of this query, a new graph is created. The
        data used for the graph is retrieved as follows
        SELECT x, y FROM rel WHERE axes...=R... ORDER BY x

        rel:      the Relation from which data will be drawn
        x,y:      the plotted attribute names
        axes:     a list of attribute names which parameterize each Graph
        select:   a dict of (a, v) where a is an axis name and v is either a value,
                  a list of values or a Selector.
        title:    a string to be used as Plot title. If not given, a title is created automatically.
        style:    this is passed to the Graph objects
        legend:   a string, used to produce the legend for each Graph.
        xlabel, x_range, ylabel, y_range: strings passed to gnuplot
        logscale: a string passed to gnuplot
        grid:     a string passed to gnuplot

        info for json output
        type:     can be "node", "network", "node2node"
        nodeid:   the id of the node when type is "node" or "node2node"
        nodeid2:  the id of the second node when type is "node2node"
        """
        self.rel = rel
        self.x = x
        self.y = y
        self.axes = axes
        self.select = select
        self.title = title
        self.style = style
        self.legend = legend
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.x_range = x_range
        self.y_range = y_range
        self.logscale = logscale
        self.grid = grid
        self.key = key
        self.stat_type = stat_type
        self.model_type = model_type
        self.unit = unit


