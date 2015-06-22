'''

Created on Jan 19, 2015

@author: George Mantakos
'''

import sqlite3 as sql
import os
import re
import csv
import logging
import json
from models.nsdplot import Table as nsdTable
from models.validation import fail, inform

DEFAULT_NODEMAP_FILE = "nodemap.json"

class Dataset(object):
    """
    A Dataset encapsulates a new in-memory database.

    Dataset objects can be used to add Table and View objects to the
    database, load data into tables and access tables and views by name.
    """
    def __init__(self):
        self.conn = sql.connect(':memory:')
        #self.conn = sql.connect('datavis.sqlite3')
        self.relations = {}

    def add(self, relation):
        """
        Add relation to the dataset.
        """
        assert isinstance(relation, Relation)
        sql_create_query = relation.sql_create()
        logging.debug("Dataset.add, Relation.sql_create: %s", sql_create_query)
        self.conn.execute(sql_create_query)
        if relation.name in self.relations:
            logging.error("In datavis.database.Dataset.add(): duplicate relation name: %s",relation.name)
            raise ValueError("This relation's name is already in use" % relation.name)            
        if hasattr(self, relation.name):
            logging.error("In datavis.database.Dataset.add(): illegal relation name: %s",relation.name)
            raise ValueError("This relation has an illegal name (already in use, or reserved)" % relation.name)
        self.relations[relation.name] = relation
        relation.dataset = self
        setattr(self, relation.name, relation)
        logging.debug("datavis.database.Dataset.add(%s)",relation.name)
        return relation

    def create_table(self, name, alist):
        """
        Create and add a Table, given name and attribute list.
        """
        return self.add(Table(name, alist))

    #TODO: cannot get column type from cursor.description
    # always returns NULL in type field, a[1]==NULL
    # even with sq.connect(":memory:",detect_types=sq.PARSE_COLNAMES | sq.PARSE_DECLTYPES)
    def get_attributes_of_relation(self, name):
        c = self.conn.cursor()
        try:
            c.execute("SELECT * FROM "+name)
            alist = [Attribute(a[0], a[1]) for a in c.description]
            return alist
        finally:
            c.close()

    def create_view(self, name, qry):
        """
        Create view and add it to the query,
        """
        view= self.add(View(name, qry))
        view.set_attributes(self.get_attributes_of_relation(name))
        return view

    def load_csv(self, filename, dialect='excel', **fmtargs):
        """
        Load data from a CSV file.

        Arguments dialect and fmtargs are passed to tbe standard csv.reader
        """
        tabdata = {}
        with open(filename,"r") as fin:
            reader = csv.reader(fin, dialect, **fmtargs)
            for row in reader:
                if row[0] not in tabdata:
                    tabdata[row[0]]=[]
                tabdata[row[0]].append(row[1:])

        for tabname in tabdata:
            table = self.relations[tabname]
            assert isinstance(table,Table)
            self.conn.executemany(table.sql_insertmany(), tabdata[tabname])

    def print_relation(self, name):
        rel = self.relations[name]
        print(rel.scheme())
        for row in self.conn.execute(rel.sql_fetch_all()):
            print(row)

    def axis_values(self, rel, attr):
        """
        Return the values of the given attribute that appear in the given relation.

        rel is either the name of a relation or a Relation object.
        attr is either the name of an attribute or an Attribute object, or a list thereof.
        """
        if not isinstance(rel, Relation):
            rel = self.relations[rel]
        if not isinstance(attr, (list, tuple)):
            attr = [attr]
        sql = rel.sql_select(attr, order=attr, distinct=True)
        return [val for val in self.conn.execute(sql)]


class StatsDatabase(Dataset):

    def __init__(self, testing=False):
        Dataset.__init__(self)
        if testing:
            alist = [
                Attribute("module", "VARCHAR"),
                Attribute("node", "INT"),
                Attribute("name", "VARCHAR"),
                Attribute("label", "VARCHAR"),
                Attribute("n_index", "INT"),
                Attribute("data", "FLOAT")
            ]
            self.create_table("dataTable", alist)
        self.nodemap = None

    def get_datatable(self):
        """
        :return: all rows of the dataTable in a list of tuples
        eg.[('module1', 1, 'outName', '', -1, 5.0), ('simlabel2', 'module1', 1, 'outName', '', -1, 5.0)]
        """
        return self.conn.execute('SELECT * from dataTable').fetchall()

    def get_nodes(self):
        """
        returns a list of all node ids in the dataTable
        """
        return list(map(lambda x: x[0], self.conn.execute('SELECT DISTINCT node from dataTable').fetchall()))

    def execute_expect_one(self, query):
        """
        executes the specified query an returns the first result as a tuple
        if there are more than one results to be returned an exception is thrown
        """
        res = self.conn.execute(query).fetchall()
        if len(res) != 1:
            raise Exception("Expecting only one result, found %d" % len(res))
        else:
            return res[0]

    def execute(self, query):
        """
        executes the specified query an returns all results in a list of tuples
        """
        return self.conn.execute(query).fetchall()

    def __generate_nodemap(self, map_file):
        """
        parse map_file and generate a nodemap
        that is a dictionary of the form {"castaliaID1":"planID1", "castaliaID12:"planID2", ...}
        :param map_file: the file containing information to generate the nodemap
        :return: the nodemap
        """
        if self.nodemap is not None:
            return
        if not os.path.exists(map_file) or not os.path.isfile(map_file):
            logging.warning("Could not load \"%s\" node mapping file" % map_file)
            return

        with open(map_file, 'r') as f:
            fjson = json.loads(f.read())
            nodes = fjson["nodes"]
            nodemap = {}
            for n in nodes:
                # print("%d = %s" % (n["simid"], n["nodeid"]))
                nodemap[str(n["simid"])] = n["nodeid"]
        self.nodemap = nodemap

    def __castaliaID_2_planID(self, castalia_id):
        """
        translate a castalia node id to a plan node id
        self.nodemap has to be generated with __generate_nodemap before this function is called or it will just return the id as is
        if castalia node id == -1 it is returned as is
        :param castalia_id: the castalia node id to translate
        :return: the plan node id (translated castalia node id)
        """
        if self.nodemap is None or castalia_id is None or castalia_id == "" or castalia_id == -1:
            return castalia_id

        if str(castalia_id) in self.nodemap:
            return self.nodemap[str(castalia_id)]
        else:
            logging.warning("castalia node id \"%s\" is not mapped to a plan id" % castalia_id)
            return castalia_id

    def __save_output(self, m, n, i, o, bl, l, v, table_name):
        """
        Stores data representing a simple output or histogram to database
            m: module
            n: node
            i: index
            o: simple output name or histogram name
            bl: sim_label
            l: label
            v: value
        """

        # ignore sim_label bl

        c = self.conn.cursor()
        # map castalia node ids to plan node ids
        n = self.__castaliaID_2_planID(n)
        i = self.__castaliaID_2_planID(i)
        c.execute("INSERT INTO %s(module,node,name,label,n_index,data) VALUES(?,?,?,?,?,?);" % table_name, (m, n, o, l, i, v))
        self.conn.commit()

    @staticmethod
    def __is_int(num):
        """
        simple function to determine if a number has floating point component
        """
        if type(num) != float: return False
        return int(num) == num

    def load_data_csv(self, table, node_mapping_file=DEFAULT_NODEMAP_FILE):
        """
        Load data from a CSV file to table
        """
        def assert_format():
            """
            checks table column number to be equal with column number in data file
            """
            file_cols = len(row)
            if file_cols != table_cols:
                fail("data file (\"%s\") format (%d columns) does not match table (\"%s\") format (%d columns)"
                    % (filename, file_cols, table.name, table_cols))

        def store_data():
            """
            stores data of a row to the appropriate table
            """
            def map_nodes():
                """
                maps castalia node ids to plan node ids, only for columns marked in table.node_mapping
                """
                for i in range(0, len(data)):
                    if table.columns[i].name in table.node_mapping:
                        data[i] = self.__castaliaID_2_planID(data[i])

            sql = "INSERT INTO %s VALUES(%s)" % (table.name, ",".join(["?"]*table_cols))
            c = self.conn.cursor()
            data = [d.strip() for d in row]
            if self.nodemap:
                map_nodes()
            c.execute(sql, tuple(data))
            self.conn.commit()

        #
        # load_data_csv
        #

        assert isinstance(table, nsdTable)
        filename = table.filename
        table_cols = len(table.columns)

        if not os.path.exists(filename) or not os.path.isfile(filename):
            fail("Could not load \"%s\" csv data file" % filename)

        # generate the castalia to plan node map
        self.__generate_nodemap(node_mapping_file)

        with open(filename, "r") as f:
            reader = csv.reader(f)
            for row in reader:
                assert_format()
                store_data()

    def load_data_castalia(self, castalia_output_file, table_name="dataTable", node_mapping_file=DEFAULT_NODEMAP_FILE):
        """
        read data from Castalia output file and store them to an sqlite db in memory
        """
        if not os.path.exists(castalia_output_file) or not os.path.isfile(castalia_output_file):
            logging.warning("Could not load \"%s\" castalia output file" % castalia_output_file)
            return

        # generate the castalia to plan node map
        self.__generate_nodemap(node_mapping_file)

        with open(castalia_output_file, "r") as f:
            lines = f.readlines()

        # prepare regex
        r_castalia = re.compile("^Castalia\|\s+(.+)$")
        r_output = re.compile("^([-+]?[0-9]*\.?[0-9]+)\s*(.*)$")
        r_histogram = re.compile("^histogram name:(.+)$")
        r_histogram_params = re.compile("histogram_min:([-+]?[0-9]*\.?[0-9]+) histogram_max:([-+]?[0-9]*\.?[0-9]+)$")
        r_histogram_values = re.compile("histogram_values\s(.+)$")
        r_simple = re.compile("^simple output name:(.+)$")
        r_simple_index = re.compile("^index:(\d+) simple output name:(.+)$")
        r_module = re.compile("^module:SN\.(.+)$")
        r_node = re.compile("^node\[(\d+)\]\.(.+)$")
        r_label = re.compile("^label:(.+)$")
        r_what = re.compile("what:(.+)$")
        r_when = re.compile("when:(.+)$")

        # parse the input
        bl = module = "Unknown"
        n = i = -1
        level = 1  # skip label
        # levels:
        # 0 - none, expect 'label'
        # 1 - label, expect 'module'
        # 2 - module, expect 'output', 'output+index', 'histogram'
        # 3 - output, expect data
        # 4 - histogram, expect min, values
        for line in lines:
            # check the 'Castalia|' prefix
            m = r_castalia.match(line)
            if m:
                line = m.group(1)
            else:
                continue

            if level == 3:
                # check for output data
                m = r_output.match(line)
                if m:
                    self.__save_output(module, n, i, o, bl, m.group(2), m.group(1), table_name)
                    continue
                else:
                    level = 2

            if level == 4:
                # check for histogram parameters
                m = r_histogram_params.match(line)
                if m:
                    histogram_min = float(m.group(1))
                    histogram_max = float(m.group(2))
                    continue

                # check for histogram values, calculate histogram properties and save values
                m = r_histogram_values.match(line)
                if m:
                    vals = m.group(1).split(" ")
                    size = len(vals) - 1
                    step = float(histogram_max - histogram_min) / size
                    curr = histogram_min
                    if self.__is_int(step): step = int(step)
                    if self.__is_int(curr): curr = int(curr)
                    ival = 0
                    for val in vals:
                        next = curr + step
                        if self.__is_int(next): next = int(next)
                        if next > histogram_max: next = "inf"
                        self.__save_output(module, n, ival, o, bl, "[" + str(curr) + "," + str(next) + ")", val, table_name)
                        curr += step
                        ival += 1
                    level = 2
                    continue

            if level == 2:
                # check for simple output declaration
                m = r_simple.match(line)
                if m:
                    i = -1
                    o = m.group(1)
                    level = 3
                    continue

                # check for simple output declaration with an index
                m = r_simple_index.match(line)
                if m:
                    i = m.group(1)
                    o = m.group(2)
                    level = 3
                    continue

                # check for histogram declaration
                m = r_histogram.match(line)
                if m:
                    o = m.group(1)
                    level = 4
                    continue

                level = 1

            if level == 1:
                # check for module declaration
                m = r_module.match(line)
                if m:
                    line = m.group(1)
                    i = -1
                    # within module declaration look for node information
                    m = r_node.match(line)
                    if m:
                        n = m.group(1)
                        module = m.group(2)
                    else:
                        module = line
                        n = -1
                    level = 2
                    continue

                level = 0

            if level == 0:
                # check for label declaration
                m = r_label.match(line)
                if m:
                    bl = m.group(1)
                    level = 1
                    continue

            if r_what.match(line) or r_when.match(line): continue
            logging.warning("Parsing file: \"%s\"\nUnknown input at level %s: %s" % (castalia_output_file, level, line))


class Attribute:
    def __init__(self, name, atype):
        self.name = name
        self.type = atype

    def sql_create(self):
        return ' '.join([self.name, self.type])


def sql_scalar(value):
    """
    Return a string mapping the python value to SQL representation.
    """
    return repr(value)


class Selector:
    """
    Selector is a utility class implementing SQL predicate generators.

    Usage:
    sel = Selector(" character_length(%(attribute)s) > 4 ")
    sel('a.name') ->  'character_length(a.name) > 4'
    sel('a.name') & sel('b.name')  -> 'character_length(a.name) > 4 AND character_length(b.name) > 4'
    """

    def __init__(self, pat):
        """pat is a string. I
        """
        self.pat = pat

    def __call__(self, attr):
        return self.pat % {'attribute': attr}

    def __and__(self, other):
        if not isinstance(other, Selector): return NotImplemented
        return AND(self, other)

    def __or__(self, other):
        if not isinstance(other, Selector): return NotImplemented
        return OR(self, other)


def approx(x, epsilon=1E-4):
    """Return a Selector for abs(%attr - x)<=epsilon*x"""
    if x == 0:
        return Selector("abs(%%(attribute)s)<=%s" % sql_scalar(epsilon))
    else:
        return Selector("abs(%%(attribute)s/%s - 1)<=%s" % (sql_scalar(x), sql_scalar(epsilon)))


def sql_binary_operator(x, op):
    """Return a Selector for '%attr op x'"""
    return Selector("%%(attribute)s %s %s" % (op, sql_scalar(x)))


def sql_boolean_binary_operator(op, *terms):
    """
    terms must be a non-empty list of Selectors, s1,...,sk.
    Returns a new Selector  of the form
    '(s1.pat op s2.pat ... op sk.pat)'
    This selector  can be used with op in ('AND', 'OR')
    """
    assert terms and all(isinstance(t, Selector) for t in terms)
    return Selector("(" + (" "+op+" ").join(t.pat for t in terms) + ")")


def less_than(x):     return sql_binary_operator(x, "<")
def less_equal(x):    return sql_binary_operator(x, "<=")
def greater_than(x):  return sql_binary_operator(x, ">")
def greater_equal(x): return sql_binary_operator(x, ">=")
def not_equal(x):     return sql_binary_operator(x, "<>")
def like(x):          return sql_binary_operator(x, "LIKE")
def not_like(x):      return sql_binary_operator(x, "NOT LIKE")
def between(a, b):    return Selector("%%(attribute)s BETWEEN %s AND %s" % (sql_scalar(a), sql_scalar(b)))


def AND(*terms):
    """
    terms: a list of Selector objects

    Return a Selector for the conjunction of terms.
    Usage:

    AND(greater_than('A'), less_than('E'))
    """
    return sql_boolean_binary_operator("AND", *terms)


def OR(*terms):
    """
    terms: a list of Selector objects

    Return a Selector for the disjunction of terms.
    Usage:

    OR(greater_than('E'), less_than('C'))
    """
    return sql_boolean_binary_operator("OR", *terms)


class Relation(object):
    """
    A base class for Table and View.

    Relation has a name and a set of attributes. It is used to compose
    SQL SELECT queries over db tables and views.
    """
    def __init__(self, name, alist):
        self.name = name
        self.set_attributes(alist)

    def set_attributes(self, alist):
        assert all(isinstance(a, Attribute) for a in alist)
        self.attributes = alist

    def sql_fetch_all(self):
        return self.sql_select(['*'])

    def __map_value(self, attr, value):
        if isinstance(value, (list, tuple)):
            return ("%s IN (" % attr) + ",".join(sql_scalar(v) for v in value) + ")"
        elif isinstance(value, Selector):
            return value(attr)
        else:
            return "%s=%s" % (attr, sql_scalar(value))

    def sql_select_clause(self, alist, distinct):
        return "SELECT " + ("DISTINCT " if distinct else "") + ','.join(alist)
    def sql_from_clause(self):
        return "FROM "+self.name
    def sql_where_clause(self, where):
        if where:
            if isinstance(where, dict):
                # make it into a list
                where = [(a,where[a]) for a in where]
            if isinstance(where, list):
                return " WHERE " + ' AND '.join([self.__map_value(attr,value) for attr,value in where])
        return ""
    def sql_order_by_clause(self,order):
        if order:
            return " ORDER BY "+','.join(order)
        return ""

    def sql_select(self, alist, where=None, order=[], distinct=False):
        """
        alist: a list of names or attributes
        where: a list of (attr, value) or a dict { attr: value }. Value can be an int,double,str,unicode, or a list of these
        order: a sublist of alist
        """

        sql = ' '.join([self.sql_select_clause(alist, distinct),
                        self.sql_from_clause(),
                        self.sql_where_clause(where),
                        self.sql_order_by_clause(order)
                        ])
        logging.debug("Relation.sql_select: " + sql)
        return sql

    def scheme(self):
        return ''.join([self.name,'(',','.join("%s %s" % (a.name, a.type) for a in self.attributes),')'])

    def axis_values(self, attr):
        return self.dataset.axis_values(self, axes)


class Table(Relation):
    """
    Table objects map SQL tables to python. They inherit from relations.
    Table objects can be used to create and load SQL tables.
    """
    def __init__(self, name, alist):
        Relation.__init__(self, name, alist)
    def sql_create(self):
        """Return a CREATE TABLE query for this table."""
        return ' '.join(['CREATE TABLE',self.name, '(',
                         ', '.join(a.sql_create() for a in self.attributes),
                         ')'])

    def sql_insertmany(self):
        """Return an INSERT ... VALUES query for this table."""
        return "INSERT INTO "+self.name+" VALUES(" + ','.join('?'*len(self.attributes))+")"


class View(Relation):
    """
    View object map SQL views to python. They inherit from Relation.
    They can be used to create SQL views.
    """
    def __init__(self, name, defquery):
        """
        name is the name of the view.
        defquery is an SQL query defining the view.
        Example:
        View('foo','SELECT A, B from BAR ORDER BY a)
        """
        Relation.__init__(self, name, [])
        self.defquery = defquery
    def sql_create(self):
        """Return a CREATE VIEW query for this view."""
        return ' '.join(['CREATE VIEW',self.name,'AS',self.defquery])

