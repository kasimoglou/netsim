'''
The Simulation Job Monitor functionality.

Created on Mar 2, 2014

@author: vsam
'''

from threading import Thread, RLock, Condition
from psycopg2.pool import ThreadedConnectionPool

import time
import logging
import os.path
from shutil import copyfile

from runner.dpcmrepo import repo
from runner.DAO import JobDao, ExecutorDao, JobStatus, SimJob, UserDao
from runner.config import monitor_init
from runner.apierrors import *
from subprocess import CalledProcessError
from simgen.executor import Executor

from models.aaa import User

class Manager:
    """A singleton class managing the whole execution engine.
    
    It is a registry for executors and monitor engines, manages the
    database connection pool and provides the service API to the gui
    and the rest of the world.
    """
    SINGLETON = None
    def __init__(self, dbconn):
        if Manager.SINGLETON is not None:
            raise RuntimeError("Attempt to create multiple MonitorManager instances")
        else:
            Manager.SINGLETON = self
            
        self.log = logging.getLogger("Manager")
            
        # set up database pool
        self.dbconn = dbconn
        self.pool = ThreadedConnectionPool(20, 100, dbconn)
        
        # prepare database to recover jobs
        self.getDao().ready_active_jobs()                        

        # create executors
        self.execs = {}            # the executor registry
        self.default_executor = None   # the default executor for jobs
        self._create_executors()

        # monitor registry
        self.monitors = {}             # the monitor registry
        self._create_monitors()

        self.log.info("Manager initialized and running")


    def _create_executors(self):
        exdao = ExecutorDao(self.pool)
        for ex in exdao.get_executors():
            if ex.name in self.execs:
                logging.critical("Duplicate executor name: %s", ex.name)
            self.execs[ex.name] = ex
            self.log.info("Registered executor %s",ex.name)
        import runner.config
        self.default_executor = self.execs[runner.config.default_executor()] 

    def _create_monitors(self):
        for name, nw in monitor_init():
            self.monitors[name] = MonitorEngine(name, nw)

        # Start the db monitoring task
        main = self.monitors['main']
        self.dbMonitor = main.add_task(DbPollTask(main))



    #---------------------
    # Public API
    #---------------------

    @staticmethod
    def initialize(dbconn):
        '''Initialize the manager with the given database URL.'''
        if Manager.SINGLETON is not None:
            return
        return Manager(dbconn)

    @staticmethod
    def shutdown():
        '''Shut down the manager.'''
        self = Manager.SINGLETON
        allmon = self.monitors.values()
        self.log.info("Disabling monitors")
        self.monitors = {}
        
        for m in allmon:
            m.shutdown()        
                
        # destroy the db connection pool
        self.log.info("Closing database session pool")
        self.pool.closeall()
        del self.pool


    @staticmethod
    def getDao():
        '''Return a DAO for this thread.'''
        return JobDao(Manager.SINGLETON.pool)

    
    @staticmethod
    def executor(name=None):
        '''Return the executor with the given name. If name is None, or
        not given, return the default executor.

        Raises KeyError if the provided name does not correspond to an executor.'''
        if name is None:
            return Manager.SINGLETON.default_executor
        else:
            return Manager.SINGLETON.execs[name]

    @staticmethod
    def executors():
        '''Return an iterable of all executors'''
        self = Manager.SINGLETON
        for ex in self.execs.values():
            yield ex
    
    @staticmethod
    def monitor_engines():
        '''Return an iterable of all monitor engines'''
        self = Manager.SINGLETON
        for ex in self.monitors.values():
            yield ex

    @staticmethod
    def create_job(exctor, url, simhome=None):
        '''
        Create a new job on the given executor and for the passed url and
        simhome.
        '''
        self = Manager.SINGLETON
        fileloc = exctor.create_simulation(url, simhome)
        Manager.getDao().submit_new_job(exctor.name, fileloc)
        return fileloc

    @staticmethod
    def delete_job(job):
        '''
        Delete a job. The job can be either a SimJob, or a fileloc
        or a simid.

        The job must be PASSIVE.
        '''
        if isinstance(job, str):
            if job.startswith('/'):
                job = Manager.get_job_by_fileloc(job)
            else:
                job = Manager.get_job_by_simid(job)
        if job.state != 'PASSIVE':
            raise Forbidden(message='Bad job status', 
                details='Cannot delete a job which is still executing')
        xtor = Manager.executor(job.executor)        
        xtor.delete_simulation(job)
        Manager.getDao().delete_job(job)

	
    @staticmethod
    def jobs():
        '''Return an iterable over all jobs'''
        dao = Manager.getDao()
        jobs = dao.get_jobs()
        dao.release()
        return jobs


    @staticmethod
    def get_job_by_fileloc(fileloc):
        '''Get the job for the given fileloc'''
        return Manager.getDao().get_job_by_fileloc(fileloc)

    @staticmethod
    def get_job_by_simid(simid):
        '''Get the job for the given fileloc'''
        fileloc = Manager.get_simhome(simid)
        return Manager.get_job_by_fileloc(fileloc)


    @staticmethod
    def copy_simfiles(nsdfile, simfile, fileloc):
        simdst = fileloc + "/sim" + ".json"
        nsddst = fileloc + "/nsd" + ".json"
        copyfile(nsdfile, nsddst)
        copyfile(simfile, simdst)
        print(fileloc) 
  
    #
    #  PR simid  =  'SIMOUTPUT':<executor-name>:<homedir-basename>
    # 

    @staticmethod
    def get_simid(xtor, simhome):
        '''Return the simulation PR id for the given simhome and executor'''
        name = xtor.name if isinstance(xtor, Executor) else xtor
        if name not in Manager.SINGLETON.execs:
            raise NotFound(details='Executor cannot be determined')
        return SimJob.make_simid(name, simhome)


    @staticmethod
    def get_simhome(simid):
        '''Return the simhome for the given simulation PR id'''
        xtor,  bname = SimJob.break_simid(simid)
        homedir = Manager.executor(xtor).homedir
        return os.path.join(homedir, bname)

    @staticmethod
    def create_user(user):
        '''Create a system system user for the given object'''
        assert isinstance(user, User)
        dao = UserDao(Manager.SINGLETON.pool)
        dao.create_user(user)

    @staticmethod
    def get_user(username):
        '''Return a system system user by this name, or None.'''
        assert isinstance(username, str)
        dao = UserDao(Manager.SINGLETON.pool)
        return dao.get_user(username)

    @staticmethod
    def get_users():
        '''Return an iterator over all system users.'''
        dao = UserDao(Manager.SINGLETON.pool)
        yield from dao.get_users()

    @staticmethod
    def update_user(username, **kwargs):
        '''Update the system user with the given username, setting
        the passed keyword arguments to the passed values.'''
        dao = UserDao(Manager.SINGLETON.pool)
        dao.update_user(username, **kwargs)

    @staticmethod
    def delete_user(username):
        '''Delete the system user with the given username.'''
        dao = UserDao(Manager.SINGLETON.pool)
        dao.delete_user(username)





class MonitorEngine:        
    '''
    A class monitoring the execution of jobs.
    
    Instances of this class act essentially as queues of tasks, which
    are instances of class MonitorTask. 
    Worker threads, which are instances of class MonitorWorker,
     get tasks and execute them. 
    '''
    
    def __init__(self, name, number_of_workers=4):
        '''
        Create an engine and initialize its database pool
        '''
        
        self.manager = Manager.SINGLETON
        
        # Make sure the name is unique
        self.name = name        
        self.log = logging.getLogger("Monitor(%s)" % name)
        self.log.info("Established in registry")
                
        # monitor lock
        self.monitor_lock = RLock()
        
        # set up register for threads
        self.task_queue = []
        self.task_queue_not_empty = Condition(self.monitor_lock)
        self.shuttingDown = False        
                        

        # worker threads
        self.workers = set()
        for i in range(number_of_workers):
            worker = MonitorWorker(self)
            self.workers.add(worker)
            worker.start()
                
        self.log.info("initialized")
        

    def add_task(self, task):
        '''
        This is the routine that adds a new task to the monitor.
        '''
        with self.monitor_lock:
            if self.shuttingDown:
                return None
            self.task_queue.append(task)
            self.task_queue_not_empty.notify()
            return task

        
    def get_task(self):
        '''
        This is a blocking call that workers use to wait on tasks.
        If it returns null, we are shutting down.
        '''
        with self.monitor_lock:
            while not (self.task_queue or self.shuttingDown):
                self.task_queue_not_empty.wait()
            if self.shuttingDown:
                return None
            assert self.task_queue
            return self.task_queue.pop(0)
        
                
    def shutdown(self):
        '''
        Shutdown the engine. Notice that this will not terminate tasks
        violently, so it may block for some time
        '''
        self.log.info("Shutting down")        
        # ok, so nothing comes into the task list
        with self.monitor_lock:
            if self.shuttingDown:  # someone beat us to it!
                return
            else:
                self.shuttingDown = True            
                self.task_queue_not_empty.notifyAll()

        # Wait on workers
        for worker in self.workers:
            worker.join()
        
        
    def getDao(self):
        return self.manager.getDao()


    def activate_job(self,job):
        pass



class MonitorWorker(Thread):
    '''
    Implements a worker thread for monitor engine
    '''
    def __init__(self, engine):
        Thread.__init__(self)
        self.engine = engine        

    def run(self):
        # repeatedly execute tasks
        while True:
            task = self.engine.get_task()
            if task is None:    # we are shutting down (?)
                return
            
            try:
                task.execute()                
            except:
                self.engine.log.exception("Task has raised an uncaught exception: %s",task.name)

        

class MonitorTask:
    '''
    An abstract base class for tasks that are controlled by a monitor engine
    '''
    def __init__(self, engine, name="task"):
        self.engine = engine
        self.name = name
        self.log = logging.getLogger(self.engine.name)
    
    def execute(self):
        '''
        This method must be overloaded by subclasses
        '''
        raise NotImplemented


#---------------------------------------------------------------------------


class DbPollTask(MonitorTask):
    '''
    The db monitor polls the database for events.
    In particular, it examines for ready jobs to activate 
    and cleans up old jobs
    '''
    def __init__(self, engine, pollingPeriod=1, max_badcount=5):
        MonitorTask.__init__(self,engine,"DbMonitor")
        self.pollingPeriod = pollingPeriod
        self.max_badcount = max_badcount
        self.badcount = max_badcount

    def execute(self):
            try:
                time.sleep(self.pollingPeriod)
                self.examineDb()
            except:
                self.log.exception("Exception in %s", self.name)
                self.badcount -= 1
                if self.badcount<=0:
                    # A series of failures, we should abort
                    self.log.critical("%s aborting.",self.name) 
                    return
            else:
                self.badcount = self.max_badcount   # reset badcount
            self.engine.add_task(self)


    def examineDb(self):
        '''
        Dispatches polled tasks for this round
        '''
        dao = self.engine.getDao()
        try:
            #self.log.debug("Cleanup of old jobs")
            #dao.cleanup_old_jobs()
            self.log.debug("Processing new jobs")
            self.processReadyJobs(dao)
        finally:
            dao.release()
        
        
    def processReadyJobs(self,dao):
        '''
        Process any new jobs in the database
        '''
        for job in dao.activate_ready_jobs():
            self.engine.add_task(ProcessJob(self.engine, job))


#
#  The main Job processing thread
#
class ProcessJob(MonitorTask):
    
    def __init__(self, engine, job):
        MonitorTask.__init__(self, engine, "[%s]" % job)
        self.job = job
        
    def execute(self):
        # execute the processor
        try:
            dao = self.engine.getDao()
            success = False
            executor = Manager.executor(self.job.executor)
            self.log.info("%s processing.", self.name)
            
            if self.job.status==JobStatus.INIT: executor.prepare_simulation(self.job.fileloc)
            elif self.job.status==JobStatus.PREPARED: executor.generate_simulation(self.job.fileloc)
            elif self.job.status==JobStatus.GENERATED: executor.compile_simulation(self.job.fileloc)
            elif self.job.status==JobStatus.COMPILED: executor.start_simulation(self.job.fileloc)
            elif self.job.status==JobStatus.STARTED: executor.finish_simulation(self.job.fileloc) 
            else: 
                # ABORTED or FINISHED
                # 
                dao.passivate_job(self.job)
                try:
                    executor = Manager.executor(self.job.executor)
                    executor.finalize(self.job.fileloc, self.job.jobid, self.job.status)
                except CalledProcessError as e:
                    self.log.warn("%s failed: %s", self.name, e.returncode)
                return

        except Exception as e:
            self.log.info("%s failed: %s", self.name, self.job.status)
            self.log.debug("%s raised an exception" % self.name, exc_info=1)            
        else:
            self.log.info("%s finished successfully", self.name)
            success = True

        # Abort the job on failure
        if not success:
            self.log.info("Abort for %s", self.name)
            dao.transition_job_status(self.job, JobStatus.ABORTED)
        else:
            # Success, update the job status
            newstatus = JobStatus.transition(self.job.status)
            dao.transition_job_status(self.job, newstatus)

        # Update the project repository object.
        job = dao.get_job_by_fileloc(self.job.fileloc) # refresh the job
        # try to update the PR sim record

        retries = 3
        while True:
            try:
                repo().update_simulation(job.simid,
                    simulation_status=job.status,
                    last_status=job.last_status,
                    tsinstatus=str(job.tsinstatus)
                    )
            except dpcmrepo.Conflict:
                retries -= 1
                if retries==0:
                    raise
            else:
                break





        