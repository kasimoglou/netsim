"""
   This is part of netsim installation scripts. Its purpose is to
   check the connection to the database provided by the user.
"""

import sys
import argparse
from psycopg2 import connect


def check_dbconn(dbconn):
    db = connect(dbconn)

    # Check postgresql version
    c = db.cursor()
    c.execute("show server_version")
    vtup = c.fetchone()[0].split(".")
    version_tuple = tuple([int(p) for p in vtup])
    assert version_tuple >= (9,3,0)

    # Check that the current user is the owner
    c.execute("""
SELECT u.usename=current_user
 FROM pg_database d
  JOIN pg_user u ON (d.datdba = u.usesysid)
 WHERE d.datname = (SELECT current_database())
""")
    assert c.fetchone()[0]

    return db


if __name__=='__main__':

    parser = argparse.ArgumentParser(description='''This program will check the connection
  to a postgresql database, for use with netsim server.''')

    parser.add_argument("dbconn", help="The database connection string for netsim server.")  

    args = parser.parse_args()


    try:
        db =check_dbconn(args.dbconn)
    except:
        sys.exit(1)


