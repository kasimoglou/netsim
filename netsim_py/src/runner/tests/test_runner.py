'''
This file is used to check the monitor.


Created on Mar 4, 2014

@author: vsam
'''

from runner.DAO import check_database, JobDao, JobStatus, ExecutorDao, UserDao
from psycopg2 import IntegrityError, InternalError
from psycopg2.pool import ThreadedConnectionPool
from models.aaa import User

import pytest
from simgen.executor import LocalExecutor
from runner.config import cfg

#
# We are assuming that the user has created a local postgresql database
# called dpcm_test 
# 

pg_testdb = "dbname=dpcmtest"

@pytest.fixture(scope='module', autouse=True)
def pg_pool(request, setup_configuration):
    class Args: pass
    args = Args()
    args.initdb = "YES"
    check_database(args, pg_testdb)
    pool = ThreadedConnectionPool(1,10, pg_testdb)
    def fin():
        pool.closeall()
    request.addfinalizer(fin)
    return pool


def test_JobDao(pg_pool):
    assert pg_pool is not None
    dao = JobDao(pg_pool)    
    assert list(dao.get_jobs()) == []
    
    # input bad Jobs
    with pytest.raises(IntegrityError):
        dao.submit_new_job("noexec", "foo")
    with pytest.raises(IntegrityError):
        dao.submit_new_job("local", None)
    
    # input a good job
    dao.submit_new_job('local', '/foo')
    
    jobs = list(dao.get_jobs())
    assert len(jobs) == 1
    job = jobs[0]

    assert job.fileloc == "/foo"
    assert job.executor == "local"
    assert job.state == "READY"
    assert job.status == JobStatus.INIT
    
    dao.activate_ready_jobs()

    jobs = list(dao.get_jobs())
    assert len(jobs) == 1
    job = jobs[0]

    assert job.fileloc == "/foo"
    assert job.executor == "local"
    assert job.state == "ACTIVE"
    assert job.status == JobStatus.INIT
    
    with pytest.raises(InternalError):
        dao.transition_job_status(job, JobStatus.GENERATED)
    with pytest.raises(InternalError):
        dao.transition_job_status(job, JobStatus.FINISHED)
    
    dao.transition_job_status(job, JobStatus.PREPARED)
    
    jobs = list(dao.get_jobs())
    assert len(jobs) == 1
    job = jobs[0]

    assert job.fileloc == "/foo"
    assert job.executor == "local"
    assert job.state == "READY"
    assert job.status == JobStatus.PREPARED
    
    # Test the acquire/release mechanism
    dao.release()
    assert dao.db is None
    c = dao.acquire()
    assert c is not None
    assert c is dao.acquire()
    dao.release()



def test_ExecutorDao(pg_pool):
    dao = ExecutorDao(pg_pool)
    
    ex = list(dao.get_executors())
    
    assert len(ex)==1
    e = ex[0]

    assert e.name == "local"
    assert isinstance(e, LocalExecutor)
    
    dao.release()
    
def test_UserDao(pg_pool):
    dao = UserDao(pg_pool)

    assert len(list(dao.get_users())) == 1

    dao.create_user(User('foo', 'bar', False))
    assert len(list(dao.get_users())) == 2

    u = dao.get_user('foo')
    assert u.username == 'foo'
    assert u.password == 'bar'
    assert u.is_admin == False

    dao.update_user('foo', password='baz')
    u = dao.get_user('foo')
    assert u.username == 'foo'
    assert u.password == 'baz'
    assert u.is_admin == False

    dao.delete_user('foo')
    assert len(list(dao.get_users())) == 1

