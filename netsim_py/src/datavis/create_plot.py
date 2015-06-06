'''
Created on Jan 19, 2015

@author: George Mantakos
'''
import logging
from subprocess import PIPE, Popen
from datavis.database import Relation

class StatBreakdownHelper:
        """
        Helper class to aid in the collection of values from the database and output them in an appropriate format for gnuplot
        Holds a list of lists in the following format
        [[node1, label1_val1, label2_val1, ...]
         [node2, label1_val2, label2_val2, ...]
         ...
        ]
        where node1 is the Node number and label1_val1 is a label's value label2_val1 is a label's value and so on
              node2 is another node,       label1_val2 is another value of the same label as label1_val1 and so on
        """
        def __init__(self):
            self.info = []
            self.label_no = 1

        def add_label_values(self, vals):
            """
            vals should be a list of tuples, each tuple should be in the format (Node, label_value)
            """
            assert isinstance(vals, list)
            assert all(isinstance(x, tuple) for x in vals)

            for row in vals:
                node = row[0]
                val = row[1]

                r = self.__get_row_with_node(node)
                if r is not None:  # node already exists in out list
                    index = r
                else:  # create a new list for our new node
                    self.info.append([node])
                    index = len(self.info)-1
                while len(self.info[index]) != self.label_no:  # check if all previous positions have been filled
                    self.info[index].append(0)                 # if not fill with zeroes to indicate there was no value for
                                                               # the specified node and label
                self.info[index].append(val)                   # add the new value for label number "label_no"
            # check for any row with a node that did not have the specific label statistic, we have to fill that with zero
            for row in self.info:
                while len(row) != self.label_no + 1:
                    row.append(0)
            self.label_no += 1

        def __get_row_with_node(self, node):
            """
            return an index to the row with id node, or None if it does not exist
            """
            i = 0
            for row in self.info:
                if row[0] == node:
                    return i
                i += 1
            return None

        def get_values_invert_columns(self):
            """
            returns the info structure sorted by node, now each list contains one column
            so if there are N columns, the first contains the node numbers, the second the values of the 1st
            label statistic, the third the values of the 2nd label statistic and so on
            """
            sorted_by_node = sorted(self.info, key=lambda x: x[0])
            ret = []
            for i in list(range(len(sorted_by_node[0]))):
                col = []
                for row in sorted_by_node:
                    col.append(row[i])
                ret.append(col)
            return ret

        def get_values(self):
            """
            returns the info structure sorted by node
            """
            if len(self.info) == 0:
                return None
            else:
                return sorted(self.info, key=lambda x: x[0])


class Plot():
    def __init__(self, title=None, xlabel=None,
                 ylabel=None, x_range=None, y_range=None, terminal=None,
                 logscale=None, grid=" ", key=None, output=None, is_histogram=False):
        self.graphs = []
        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.x_range = x_range
        self.y_range = y_range
        self.terminal = terminal
        self.logscale = logscale
        self.grid = grid
        self.key = key
        self.output = output
        self.is_historgram = is_histogram

    def make_plot(self, gnuplot="gnuplot"):
        p = Popen(gnuplot, stdin=PIPE)
        ret = False
        try:
            script = self.__create_script()
            if script:
                p.stdin.write(script.encode("utf-8"))
                ret = True
        # except Exception:  #  for debugging
        #     import traceback
        #     print(traceback.format_exc())
        finally:
            p.stdin.close()
            return ret

    def make_parameter(self):
        return self.graphs[0].output_data()

    def __create_script(self):
        script = ""
        if self.title:    script += ('set title ' + '"'+self.title+'"\n')
        if self.xlabel:   script += ('set xlabel "' + self.xlabel + "\n")
        if self.ylabel:   script += ('set ylabel "' + self.ylabel + '"\n')
        if self.x_range:  script += ('set xrange ' + self.x_range + "\n")
        if self.y_range:  script += ('set yrange ' + self.y_range + "\n")
        if self.logscale: script += ('set logscale %s' % self.logscale + "\n")
        if self.grid:     script += ('set grid %s' % self.grid + "\n")
        if self.key:      script += ("set key %s" % self.key + "\n")
        if self.terminal: script += self.terminal.out(self.output)
        if self.is_historgram: script += ("set style data histograms\n"
                                          "set style histogram cluster gap 2\n"
                                          "set style fill solid 1.0\n")

        script += ("plot" + ','.join([g.output_plot() for g in self.graphs]) + "\n")
        if self.is_historgram:
            sbh = StatBreakdownHelper()
            for g in self.graphs:
                sbh.add_label_values(g.output_data())
            values = sbh.get_values()
            if not values:
                return None
            for i in range(len(values[0])-1):
                for row in values:
                    node = str(row[0])
                    val = str(row[i+1])
                    script += ("\""+node+"\""+" "+val+"\n")
                script += "end\n"
        else:
            has_data = False
            for g in self.graphs:
                graph_data = g.output_data_for_gnuplot()
                if graph_data is not None:
                    script += graph_data
                    has_data = True
            if not has_data:
                return None

        return script

    def add_graph(self, rel, x, y, select={}, title=None, style='linespoints'):
        g  = Graph(self, rel, x, y, select=select, title=title, style=style)
        return self


class Graph(object):
    def __init__(self, plot, rel, x, y, select=[], title=None, style='linespoints'):
        self.plot = plot
        plot.graphs.append(self)

        self.relation = rel
        assert isinstance(rel, Relation) and rel.dataset is not None

        self.x = x
        self.y = y

        self.select = select
        self.title = title
        self.style = style

    def __default_title(self):
        return str(self.select)

    def __output_style(self):
        if callable(self.style):
            return self.style(self.select)
        else:
            return str(self.style)

    def output_plot(self):
        title = self.__default_title() if self.title is None else self.title
        style = "" if self.style is None or self.style == "histogram" else "with "+self.__output_style()
        using = "using 2:xticlabels(1)" if self.style == "histogram" else ""
        return """ '-' %s title "%s" %s""" % (using, title, style)

    def output_data_for_gnuplot(self):
        """
        writes this graph's data, in gnuplot format, to string s
        returns s or None if no data was returned from the query
        """
        s = ""
        sql = self.relation.sql_select([self.x[0].name, self.y[0].name], where=self.select, order=[self.x[0].name])
        conn = self.relation.dataset.conn
        res = conn.execute(sql).fetchall()
        logging.debug("query row count: %d" % len(res))
        if len(res) == 0: return None
        for row in res:
            s += (" ".join(str(x) for x in row) + "\n")
        s += "end\n"
        return s

    def output_data(self):
        """
        fetches this graph's data and returns them as a list of tuples
        "graph" can represent a graph plot (linespoints, bar chart etc) or only statistics' values
        """
        # we may have multiple columns in tuple x as well as in y
        # we may also have x==None
        col_names = []
        if self.x is not None:
            for i in self.x: col_names.append(i.name)
        if self.y is not None:
            for i in self.y: col_names.append(i.name)

        logging.root.critical("col_names=%s", col_names)

        if self.x is not None:
            o = [i.name for i in self.x]
        elif self.y is not None:  # applicable when x is None
            o = [i.name for i in self.y]
        else:  # should never occur, just in case
            o = []
        sql = self.relation.sql_select(col_names, where=self.select, order=o)
        logging.root.debug("SQL='%s'",sql)
        try:
            conn = self.relation.dataset.conn
            results =  conn.execute(sql).fetchall()
        except:
            logging.root.critical("IT THROWS")
            raise
        logging.root.debug("Results=%s", results)
        return results


DEFAULT = "DEFAULT"


def default_title(x, y, axes, axisvalues):
    x = x[0].name
    y = y[0].name
    title = "   "+x+" over "+y+"   "
    sva = []
    for a in axes:
        if len(axisvalues[a]) == 1:
            sva.append((a, list(axisvalues[a])[0]))
    if sva:
        title += "(" + ','.join("%s=%s" % (a, str(v)) for a, v in sva) + ")"
    return title

pm_defaults = {
    "select": {},
    "title": DEFAULT,
    "style": "linespoints",
    "legend": DEFAULT,
    "xlabel": None,
    "ylabel": None,
    "x_range": None,
    "y_range": None,
    "terminal": None,
    "logscale": None,
    "grid": " ",
    "key": None,
    "output": DEFAULT,
    "x": None
}

def make_plot(rel, x, y, axes, select={}, title=DEFAULT, style='linespoints',
              legend=DEFAULT,
              xlabel=None, ylabel=None, x_range=None, y_range=None,
              terminal=None, logscale=None, grid=" ", key=None,
              output=DEFAULT, is_histogram=False):
    """
    Return a Plot object, containing a number of Graph objects.

    The graphs contained in the plot are produced as follows:
    First, the following query (in pseudo-SQL) is executed
    SELECT DISTINCT axes... FROM rel WHERE select... ORDER BY axes...

    For each result row R of this query, a new graph is created. The
    data used for the graph is retrieved as follows
    SELECT x, y FROM rel WHERE axes...=R... ORDER BY x

    rel: the Relation from which data will be drawn
    x,y: the plotted attribute names
    axes: a list of attribute names which parameterize each Graph
    select: a dict of (a, v) where a is an axis name and v is either a value,
         a list of values or a Selector.
    title: a string to be used as Plot title. If not given, a title is created automatically.
    style: this is passed to the Graph objects
    legend: a string, used to produce the legend for each Graph.
    xlabel, x_range, ylabel, y_range: strings passed to gnuplot
    logscale: a string passed to gnuplot
    grid: a string passed to gnuplot
    terminal: an object used to select and configure a gnuplot terminal
    output: a string used to create output file of gnuplot
    """

    if axes is not None:
        # set of per-attribute values
        axisvalues = {axis: set([]) for axis in axes}

        # compute set of all axis values
        axisdata = rel.dataset.conn.execute(rel.sql_select(axes, where=select, order=axes, distinct=True)).fetchall()

        # fill axis values
        for row in axisdata:
            for axis, value in zip(axes, row):
                axisvalues[axis].add(value)

    # set the plot title
    if title == DEFAULT:
        title = default_title(x, y, axes if axes is not None else [], axisvalues if axes is not None else None)

    if output == DEFAULT and x is not None and y is not None:
        wc = rel.sql_where_clause(select)
        output = rel.name+':'+y[0].name+'('+x[0].name+')'+wc + ("_hist" if style == "histogram" else "")
    output = output.replace(' ', '.')

    if xlabel is None and x is not None: xlabel = x[0].name
    if ylabel is None and y is not None: ylabel = y[0].name

    if axes is not None:
        # prepare the legend titles
        if legend == DEFAULT:
            legend = ','.join("%s=%%(%s)s" % (axis, axis) for axis in axes if len(axisvalues[axis])>1)

    # create the plot
    plot = Plot(title=title,
                xlabel=xlabel, ylabel=ylabel,
                x_range=x_range, y_range=y_range,
                terminal=terminal, logscale=logscale, grid=grid, key=key,
                output=output, is_histogram=style == "histogram")

    if axes is not None:
        # make the graphs
        for row in axisdata:
            sel = dict(zip(axes, row))
            plot.add_graph(rel, x, y, select=sel, title=(legend%sel), style=style)
    else:
        plot.add_graph(rel, x, y, select=select, title=title, style=style)
    return plot





#
# Terminal implementations for gnuplot
#


class PNG:
    def __init__(self, filename=None, size=(1024, 768)):
        self.filename = filename
        self.size = size

    def out(self, filebase=None):
        fname = self.filename if self.filename else filebase+'.png' if filebase else None

        ret = "set terminal png size %d,%d\n" % self.size
        if fname:
            ret += "set output \""+fname+"\"\n"
        return ret


class Tikz:
    def __init__(self, filename=None, size=None):
        self.filename = filename
        self.size = size
    def out(self,filebase=None):
        fname = self.filename if self.filename else filebase+'.tex' if filebase else None

        ret = "set terminal tikz"
        if self.size:
            ret += " size %s" % self.size
        ret += "\n"
        if fname:
            ret += "set output \""+fname+"\"\n"
        return ret

