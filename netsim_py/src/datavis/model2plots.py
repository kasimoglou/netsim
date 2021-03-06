#
# NSD model to plots for Castalia
#

from models.nsdplot import PlotModel, Table, DerivedTable, ColumnExpr, \
    ConstantExpr, ColumnRef, Operator
from datavis.database import StatsDatabase
from datavis.create_plot import make_plot, PNG, default_title
from datavis.results2json import plot2json, JsonOutput, parameter2json
from models.validation import Context, warn, inform, fail, fatal
from datavis.database import Attribute
import logging
import traceback


def collect_tables(tables, tlol, table):
    """
    Add a table to tables and lexical order
    """
    if table in tables: return
    tables.add(table)

    if isinstance(table, DerivedTable):
        for basetable in table.base_tables:
            assert isinstance(basetable, Table)
            collect_tables(tables, tlol, basetable)

    tlol.append(table)


def collect_tables_for_pml(pml):
    """
    Return a set of Table instances used for the list of plots.
    """
    tables = set()
    tlol = []
    for pm in pml:
        collect_tables(tables, tlol, pm.rel)

    return tlol


def expression2sql(expr, prec_table=False):
    """
    transforms an expression to the corresponding sql
    returns None if some error occurred
    """
    if isinstance(expr, ConstantExpr):
        return str(expr.value)
    elif isinstance(expr, ColumnRef):
        if prec_table:
            return expr.column.table.name + "." + expr.column.name
        else:
            return expr.column.name
    elif isinstance(expr, Operator):
        func = expr.function
        if func.isinline:
            sql = "(" + (" " + func.name + " ").join(list(
                map(lambda x: expression2sql(x, prec_table) if not isinstance(x, str) else x, expr.operands))) + ")"
        elif func.isaggregate:
            x = expr.operands[0]
            sql = func.name + "(" + (expression2sql(x, prec_table) if not isinstance(x, str) else x) + ")"
        else:
            try:
                raise Exception("Operator should be either inline or aggregate")
            except Exception:
                logging.critical(traceback.format_exc())
            return None
        return sql
    elif isinstance(expr, ColumnExpr):
        return expression2sql(expr.expr, prec_table) + " AS " + expr.alias
    elif expr is None:
        return ""
    else:
        # This should never happen, expression parsing should have generated a valid expression or handle possible errors
        logging.critical(traceback.format_exc())
        fail("unknown expression type \"%s\"" % type(expr).__name__, ooc=TypeError)


def get_select_columns(col):

    if isinstance(col, ColumnExpr):
        ret = expression2sql(col, prec_table=True)
        if ret is None:
            # This should only happen if there was some error in expression parsing, and the expression passed to
            # expression2sql is malformed
            fail("error in views generation")
    else:
        if col.origin_table:
            ret = col.origin_table.name + "." + col.name
        else:
            ret = col.name
    return ret


def derived2sql(dt):
    """
    generates an sql query to be used in the creation of the derived table as a view
    SELECT ... FROM ... WHERE ... GROUPBY
    """
    assert isinstance(dt, DerivedTable)
    sql = "SELECT " + ",".join(list(map(get_select_columns, dt.columns)))
    sql += " FROM " + ",".join(list(map(lambda x: x.name, dt.base_tables)))
    if dt.table_filter:
        where_expr = expression2sql(dt.table_filter)
        if where_expr is None:
            # This should only happen if there was some error in expression parsing, and the expression passed to
            # expression2sql is malformed
            fail("error in views generation")
        sql += " WHERE " + where_expr
    if dt.groupby:
        sql += " GROUP BY " + ",".join(list(map(lambda x: x.name, dt.groupby)))

    return sql


def create_view_for_derived(ds, dt):
    """
    Create an SQL view in ds for given DerivedTable dt.
    """
    sql = derived2sql(dt)
    try:
        ds.create_view(dt.name, sql)
    except BaseException as ex:
        # this should be here to catch unhandled sql syntax errors
        fail(ex)


def create_table(ds, dt):
    """
    Creates a Table in ds for given Table dt
    """

    assert isinstance(dt, Table)
    alist = [Attribute(c.name, c.type) for c in dt.columns]
    ds.create_table(dt.name, alist)


def create_plot_for_model(pm, ds, jo):
    """
    Create a plot/parameter(statistic) for given PlotModel and StatsDatabase ds
    add generated values to JsonOutput jo
    """
    assert isinstance(pm, PlotModel)
    terminal = PNG()
    output = "DEFAULT"
    plot = make_plot(ds.relations[pm.rel.name], pm.x, pm.y, pm.axes, pm.select, pm.title, pm.style,
                     pm.legend, pm.xlabel, pm.ylabel, pm.x_range, pm.y_range,
                     terminal, pm.logscale, pm.grid, pm.key, output)

    if pm.title == "DEFAULT":
        if pm.model_type == "plot":
            pm.title = default_title(pm.x, pm.y, pm.axes if pm.axes else [],
                                     {axis: set([]) for axis in pm.axes} if pm.axes else None).lstrip().rstrip()
        elif pm.model_type == "parameter":
            # no default title for parameters
            pass

    if pm.model_type == "plot":
        # generate the plot to the current working directory
        if plot.make_plot():
            # add plot to JsonOutput jo
            plot2json(jo, pm, plot.output + ".png")
            inform("generated successfully")
    elif pm.model_type == "parameter":
        # generate the parameter (statistic)
        res = plot.make_parameter()
        if len(res) != 0 and res[0] != (None,):
            # add the parameter to JsonOutput jo
            parameter2json(jo, pm, res)
            inform("generated sucessfully")
        else:
            warn("no data found")

    else:
        logging.error("invalid model type: \"%s\"" % pm.model_type)
        fail("invalid model type: \"%s\"" % pm.model_type)


def populate_table(ds, table, castalia_data=None):
    """
    load data appropriate for this table in database ds
    if castalia_data is set, override the table's filename
    """
    if table.format == "dataTable":
        ds.load_data_castalia(table.filename if castalia_data is None else castalia_data, table.name)
    elif table.format == "csv":
        ds.load_data_csv(table)
    else:
        fail("unknown format %s" % table.format)


def model2plots(pml, jo, castalia_data=None):
    """Accepts a list of PlotModel objects and creates the corresponding plots/parameters(statistics).
    """

    assert isinstance(pml, list)
    assert all(isinstance(pm, PlotModel) for pm in pml)

    # Collect a list of tables, ordered according to dependence
    table_list = collect_tables_for_pml(pml)

    # Create database
    ds = StatsDatabase()

    # create tables
    for table in table_list:
        if isinstance(table, Table) and not isinstance(table, DerivedTable):
            with Context(view=table.name):
                create_table(ds, table)
                populate_table(ds, table, castalia_data)


    # create views
    for table in table_list:
        if isinstance(table, DerivedTable):
            with Context(view=table.name):
                create_view_for_derived(ds, table)

    # create plots
    for pm in pml:
        if pm.rel.name in ds.relations:
            with Context(view=pm.rel.name, plot=pm.title):
                create_plot_for_model(pm, ds, jo)
        else:
            fail("View %s does not exist in database, some error occurred during its generation" % pm.rel.name)


def create_simulation_results(simulation_id, plotModels, castalia_data=None):
    """
    generates plots, calculates statistics, ands returns all that info in json format
    :param simulation_id: the id of the current simulation
    :param plotModels: this object describes the plots and parameters (statistics) to be generated
    :param castalia_data: this is the path to the castalia output file
    :return: the results in json format, a python dictionary
    """
    # create the JsonOutput object that will hold all our results in json format
    jo = JsonOutput("simulation_results", simulation_id)
    # generate plots and parameters (statistics), add the results to JsonOutput jo
    model2plots(plotModels, jo, castalia_data)

    return jo.get_json()
