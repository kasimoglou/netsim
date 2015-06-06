'''
Created on Mar 2, 2014

@author: vsam
'''

from contextlib import contextmanager
from psycopg2 import connect
import psycopg2.extensions as pg
import logging
import os.path


from simgen.executor import instantiate_executor
from models.aaa import User


#---------------------------------------------------------


class State:
    '''
    An enumeration for job state
    '''
    PASSIVE = 'PASSIVE'
    READY = 'READY'
    ACTIVE = 'ACTIVE'


class JobStatus:
    '''
    An enumeration class for job status (workflow stage).
    '''
    INIT = 'INIT'
    PREPARED = 'PREPARED'
    GENERATED = 'GENERATED'
    COMPILED = 'COMPILED'
    STARTED = 'STARTED'
    FINISHED = 'FINISHED'
    ABORTED = 'ABORTED'

    TRANSITION = {
                  'INIT' : 'PREPARED',
                  'PREPARED' : 'GENERATED',
                  'GENERATED' : 'COMPILED',
                  'COMPILED' : 'STARTED',
                  'STARTED' : 'FINISHED',
                  'FINISHED' : None,
                  'ABORTED' : None
                  }

    @staticmethod
    def transition(status):
        return JobStatus.TRANSITION[status] 
    
#---------------------------------------------------------

    
    
class SimJob(object):
    '''
    This class implements the control API for simulation jobs.
    It is essentially a proxy for the jobId and the corresponding 
    execution engine
    '''
    def __init__(self, jobid, executor, fileloc, state, 
                 status, last_status,
                 tscreated, tsinstatus):
        '''
        Create a new instance of SimJob
        '''
        
        
        self.jobid = jobid          # the id
        self.executor = executor    # the job executor
        self.fileloc = fileloc      # the unique file location (an absolute path to a directory)
        self.state = state          # the current state (active, passive or ready)
        
        # workflow state-related
        self.status = status        # the workflow position (look at JobStatus)    
        self.last_status = last_status # The status before the current one
        self.tscreated = tscreated  # timestamp of creation time
        self.tsinstatus = tsinstatus  # timestamp of time the job entered its current status
        
        self.simid = self.make_simid(executor, fileloc)

        
    def __str__(self):
        return "SimJob(%s, %s)" % (self.jobid, self.status)

    @staticmethod
    def all_columns():
        return ('jobid', 'executor', 'fileloc', 'state', 'status', 'last_status', 'tscreated', 'tsinstatus')

    SELECT_ALL='jobid, executor, fileloc, state, status, last_status, tscreated, tsinstatus'

    @classmethod
    def fromCursor(cls, cursor):
        '''
        Returns an iterable which yields elements created from the cursor.
        '''        
        for tuple in list(cursor):
            yield cls(*tuple)

    @staticmethod
    def make_simid(xtorname, fileloc):
        '''
        Returns a project-repository simulation id, given the executor name and fileloc.
        '''
        return "SIMOUTPUT:%s:%s" % (xtorname, os.path.basename(fileloc))

    @staticmethod
    def break_simid(simid):
        '''
        Returns the executor name and basename(fileloc), for a project-repository simulation id.
        '''
        if not simid.startswith('SIMOUTPUT:'):
            raise ValueError('Bad prefix in simid')
        pos = simid.index(':', 10)
        return simid[10:pos], simid[pos+1:]


#---------------------------------------------------------

        

@contextmanager
def transaction(connection):
    """Return a transaction proxy for the given db connection.""" 
    cursor = connection.cursor()
    try:
        yield cursor
    except:
        connection.rollback()
        logging.critical('Rolled back tx')
        raise
    else:
        connection.commit()
    finally:
        if cursor.closed:
            raise RuntimeError("yielding closed cursor?")
#---------------------------------------------------------


def execSql(cursor, sql, *args, **kwargs):
    '''Execute a query.
    Returns the cursor.
    '''
    if args and kwargs:
        raise ValueError("Either all positional or all keyword arguments required")
    if args:
        cursor.execute(sql, args)
    elif kwargs:
        cursor.execute(sql, kwargs)
    else:
        cursor.execute(sql)
    return cursor

#---------------------------------------------------------

    
def callSql(cursor, name, *args):
    '''Call an sql function on the cursor.
    Returns the cursor.
    '''
    a = ','.join(['%s']*len(args))
    cursor.execute("select %s(%s)" % (name,a), args)
    #cursor.callproc(name, *args)
    return cursor
    

#---------------------------------------------------------


class DataAccessObject:
    """Base class for DAOs.
    """
    def __init__(self, pool):
        self.pool = pool
        self.db = None
        
    def __del__(self):
        self.release()
        

    def release(self):
        if self.db is not None:
            # Check to see if we need to commit the transaction
            if self.db.get_transaction_status() in (pg.TRANSACTION_STATUS_ACTIVE, pg.TRANSACTION_STATUS_INTRANS):
                self.db.commit()
            
            self.pool.putconn(self.db)
            self.db = None
        
    def acquire(self):
        if self.db is None:
            self.db = self.pool.getconn()

        return self.db
            



class JobDao(DataAccessObject):
    '''
    Data access object for the job monitor database
    '''
    
    def __init__(self, pool):
        super().__init__(pool)
        
    def cleanup_old_jobs(self):
        '''
        Remove any old jobs in the database
        '''
        with transaction(self.acquire()) as cur:
            callSql(cur, 'monitor.cleanup_old_jobs')

    # Some SQL strings
    SQL_ALL = ' '.join(["select ", SimJob.SELECT_ALL, " from monitor.simjob"])
    SQL_ALL_BY_STATUS = SQL_ALL + " where status=%s"
    SQL_ALL_BY_FILELOC = SQL_ALL + " where fileloc=%s"

    def get_jobs(self):
        with transaction(self.acquire()) as cur:
            execSql(cur, self.SQL_ALL+" order by tscreated")
            return SimJob.fromCursor(cur)

    def get_jobs_by_status(self, status):
        with transaction(self.acquire()) as cursor:
            execSql(cursor,self.SQL_ALL_BY_STATUS,status)
            return SimJob.fromCursor(cursor)

    def activate_ready_jobs(self):
        with transaction(self.acquire()) as cursor:
            execSql(cursor, "select * from  monitor.activate_ready_jobs()")
            return SimJob.fromCursor(cursor)

    def ready_active_jobs(self):
        with transaction(self.acquire()) as cursor:
            execSql(cursor, "select * from monitor.ready_active_jobs()")
            return SimJob.fromCursor(cursor)

    def transition_job_status(self, job, newstatus):
        with transaction(self.acquire()) as cur:
            callSql(cur, "monitor.transition_job_status", job.jobid, job.status, newstatus)
        job.status = newstatus

    def passivate_job(self, job):
        with transaction(self.acquire()) as cursor:
            execSql(cursor, "select monitor.set_job_state(%s,%s);", job.jobid, State.PASSIVE)
            
    def submit_new_job(self, executor, fileloc):
        with transaction(self.acquire()) as cur:
            callSql(cur, "monitor.new_job", executor, fileloc)
            
    def get_job_by_fileloc(self, fileloc):
        '''Return a job object for this fileloc, or None if there is no such job.'''
        with transaction(self.acquire()) as cursor:
            execSql(cursor,self.SQL_ALL_BY_FILELOC,fileloc)
            results = list(SimJob.fromCursor(cursor))
            return results[0] if results else None

    
    def delete_job(self, job):
        with transaction(self.acquire()) as cur:
            callSql(cur, "monitor.delete_job", job.fileloc)




    
class ExecutorDao(DataAccessObject):
    """DAO for executors.
    """
    def __init__(self, pool):
        super().__init__(pool)
    
    def get_executors(self):
        import json
        with transaction(self.acquire()) as cursor:
            execSql(cursor, "select name, pyclass, home, args from monitor.executor")
            for tup in cursor.fetchall():
                name, className, homedir, args = tup
                if isinstance(args, str):
                    import json
                    args = json.loads(args)
                yield instantiate_executor(name, className, homedir, args)
                        
                

class MonitorDao(DataAccessObject):
    """DAO for executors.
    """
    def __init__(self, pool):
        super().__init__(pool)
    
    def get_monitors(self):
        import json
        with transaction(self.acquire()) as cursor:
            execSql(cursor, "select name, workers from monitor.monitor_engine")
            for tup in cursor.fetchall():
                yield tup
                


class UserDao(DataAccessObject):
    "DAO for users"
    def __init__(self, pool):
        super().__init__(pool)

    def get_users(self):
        with transaction(self.acquire()) as cursor:
            execSql(cursor, "select username, password, is_admin from monitor.user")
            for tup in cursor.fetchall():
                yield User(tup[0], tup[1], tup[2])

    def get_user(self, username):
        with transaction(self.acquire()) as cursor:
            execSql(cursor, 
                "select username, password, is_admin from monitor.user where username=%s", 
                username)
            
            tup = cursor.fetchone()
            return User(* tup) if tup else None

    def create_user(self, user):
        with transaction(self.acquire()) as cursor:
            execSql(cursor, 
                "insert into monitor.user(username, password, is_admin) values(%s, %s, %s)",
                user.username,user.password,user.is_admin)

    def update_user(self, username, **kwargs):
        # create query
        if not kwargs: return
        assert all(k in {'password', 'is_admin'} for k in kwargs)
        qry = "update monitor.user set " 
        qry +=  ','.join("%s = %%(%s)s" % (k,k) for k in kwargs)
        qry += " where username=%(username)s"
        kwargs['username'] = username

        with transaction(self.acquire()) as cursor:
            logging.info("qyery: %s  kwargs: %s", qry, kwargs)
            execSql(cursor, qry, **kwargs)

    def delete_user(self, username):
        with transaction(self.acquire()) as cursor:
            execSql(cursor, 
                "delete from monitor.user where username=%s",
                (username,))



        
#---------------------------------------------------------


def check_database(args, pgconn):
    '''
    Check that we can connect to the database and that the schema is loaded.
    '''
    
    # this will raise an exception if connection fails
    db = get_connection(args,pgconn)    
    schema_exists = check_schema_exists(args, db)
    
    if args.initdb=='NO' and not schema_exists:
        raise RuntimeError("The database does not contain the necessary schema.\n"+
                           "Please rerun with the suitable --initdb option.\n"+
                           "Use the -h option for details.")
        
    if args.initdb=='YES' or not schema_exists:
        # create the schema
        try:
            # read the contents of the sql files
            sqlfile = os.path.dirname(__file__)+"/create.sql"
            with open(sqlfile,'r') as f:
                create_sql = '\n'.join(f.readlines())

            sqlfile = os.path.dirname(__file__)+"/drop.sql"
            with open(sqlfile,'r') as f:
                drop_sql = '\n'.join(f.readlines())

            
            # make sure we are fresh
            db.commit()
            c = db.cursor()
            try:
                logging.info("Rebuilding database schema")
                c.execute(drop_sql)
                c.execute(create_sql)
                logging.info("Loading initial configuration in database")
                
                from runner.config import cfg, executor_init, monitor_init
                import json
                
                for name, className, homedir, args in executor_init():
                    c.callproc("monitor.new_executor", (name,className, homedir, json.dumps(args)))
                for name, workers in monitor_init():
                    c.callproc("monitor.new_monitor_engine", (name, workers))
                
                db.commit()                
            except:
                logging.critical("Failed to rebuild database schema")
                db.rollback()
                raise
            finally:                
                c.close()
            
        except:
            logging.critical("Creation of the database schema has failed for unknown reasons.")            
            raise        
    
    else:
        logging.info("Found existing database")
    
    
def get_connection(args,pgconn):
    try:
        db = connect(pgconn)
    except:
        raise RuntimeError("The database configuration is not functional.\n"+
                           "Please edit dpcm_sim_runner_config.py with a\n"+
                           "functional Postgresql connection")
    else:
        return db    

def check_schema_exists(args, db):
    try:         
        c = db.cursor()        
        c.execute(JobDao.SQL_ALL)
    except:
        logging.exception("Error accessing database")
        # the tables do not seem to exist
        return False
    else:
        return True
    finally:
        c.close()
