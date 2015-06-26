'''
Test module for nsd

Created on Nov 03, 2014

@author: GeoMSK
'''

import pytest

from models.nsdplot import Column, Table, Function,\
    Expression, Operator, ColumnExpr, ConstantExpr, ColumnRef, DerivedTable, DATA_TABLE, EQ


def test_column():
    col = Column("test_col")
    t = Table("t", [col])
    assert col.name == "test_col"
    col.table = t
    assert col.table == t
    assert t.columns[0] == col

    with pytest.raises(Exception):
        Column(3)
        Column("col").table = "table"


def test_table():
    col1 = Column("col1")
    col2 = Column("col2")
    t = Table("t", [col1, col2])
    assert t.columns[0] == col1
    assert t.columns[1] == col2
    assert col1.table == t
    assert col2.table == t

    with pytest.raises(Exception):
        Table(["col1", "col2"])

def test_function():
    assert Function("plus", False).name == "plus"
    assert not Function("plus",False).isaggregate
    assert Function("plus",False, True).isaggregate


def test_expression():
    Expression()


def test_operator():

    p = Function("plus", False)
    a = ConstantExpr(3)
    b = ConstantExpr(5)
    op = Operator(p, [a, b])
    assert op.operands[0] == a
    assert op.operands[1] == b
    assert a.parent == op
    assert b.parent == op


def test_columnexpr():
    ce = ColumnExpr("a", Expression())


def test_constantexpr():
    assert ConstantExpr(5).value == 5
    assert ConstantExpr("test").value == "test"


def test_derivedtable():
    t1 = Table("t1", [Column("a"), ColumnExpr("c", Expression())])
    t2 = Table("t2", [Column("b")])
    col1 = Column("col1")
    col2 = Column("col2")
    e = Expression()
    dt = DerivedTable("dt", [col1, col2], [t1, t2], e, [col1])
    assert dt.name == "dt"
    assert dt.columns[0].name == "col1"
    assert dt.columns[1].name == "col2"
    assert dt.base_tables == [t1, t2]
    assert dt.table_filter == e
    assert dt.groupby == [col1]


def test_columnref():
    cl = ColumnRef(DATA_TABLE.columns[3])
    assert cl.column.name == "label"


def test_datatable():
    dt = DATA_TABLE

    assert dt.col["name"].name == "name"