--
--  Create the schema for the job driver
--

DROP SCHEMA IF EXISTS monitor CASCADE;

CREATE SCHEMA monitor;
SET search_path TO monitor,public;


--
-- Executors
--
CREATE TABLE monitor.executor
(
	name    text primary key,
	pyclass text not null,
	home    text not null,
	args    json not null default '{}'
);


CREATE FUNCTION  monitor.new_executor(name text, pyclass text, home text, args json) RETURNS void AS '
  INSERT INTO monitor.executor(name,pyclass,home,args) VALUES($1, $2, $3, $4);
' LANGUAGE SQL;


--
--  Monitors
-- 
CREATE TABLE monitor.monitor_engine
(
	name     text  primary key,
	workers integer  CHECK(workers >= 0)
);


CREATE FUNCTION  monitor.new_monitor_engine(name text, workers integer) RETURNS void AS '
  INSERT INTO monitor.monitor_engine(name,workers) VALUES($1, $2);
' LANGUAGE SQL;


--
-- The status of a job, determines the current position in the workflow
-- 
CREATE TYPE monitor.JobStatus as ENUM('INIT','PREPARED', 'GENERATED', 'COMPILED','STARTED','FINISHED','ABORTED');

--
-- The state of a job determines whether the job is active in the monitor, passive (temporarily
-- frozen on disk)  or ready to activate 
-- 
CREATE TYPE monitor.State as ENUM('PASSIVE', 'READY', 'ACTIVE');

--
-- The main job table
--
CREATE TABLE monitor.simjob
(
	jobid bigserial primary key,
	executor text references monitor.executor(name),
	fileloc text NOT NULL UNIQUE,
	state State NOT NULL DEFAULT 'READY',

	status  JobStatus NOT NULL DEFAULT 'INIT',
	last_status JobStatus DEFAULT null,
	tscreated timestamp NOT NULL,
	tsinstatus timestamp NOT NULL
	
);


--
-- Change the state on a job and return the whole tuple. An error is raised if jid is
-- not the jobid of an actual job 
--
CREATE FUNCTION monitor.set_job_state(jid bigint, newstate monitor.State) RETURNS monitor.simjob AS $$
	DECLARE
		r   monitor.simjob%rowtype;
	BEGIN
		UPDATE monitor.simjob SET state=newstate WHERE jobid=jid
		RETURNING * INTO STRICT r;
		RETURN r;
	END
$$ LANGUAGE plpgsql;


--
-- Activate and return all READY jobs.
--
CREATE FUNCTION monitor.activate_ready_jobs() RETURNS SETOF simjob AS
$$
	UPDATE monitor.simjob SET state='ACTIVE' WHERE state='READY'
	RETURNING *;
$$ LANGUAGE SQL;


--
-- Make all active jobs ready
--
CREATE FUNCTION monitor.ready_active_jobs() RETURNS SETOF simjob AS
$$
	UPDATE monitor.simjob SET state='READY' WHERE state='ACTIVE'
	RETURNING *;
$$ LANGUAGE SQL;



--
-- Create a new job for the given file location. The job starts at INIT status and READY state
--
CREATE FUNCTION  monitor.new_job(exec text, floc text) RETURNS bigint AS '
  INSERT INTO monitor.simjob(executor, fileloc, tscreated, tsinstatus) VALUES($1, $2, NOW(), NOW()) RETURNING jobid;
' LANGUAGE SQL;


--
-- Delete a job for the given file location. The job must be in 'PASSIVE' state
--
CREATE FUNCTION monitor.delete_job(floc text) RETURNS void AS $$
	DECLARE
		ctime timestamp := current_timestamp;
		jstate monitor.State;
	BEGIN
		SELECT state INTO STRICT jstate FROM monitor.simjob WHERE fileloc = floc;
		IF jstate != 'PASSIVE' THEN
			RAISE EXCEPTION  'cannot delete job % it is not passive', floc;
		END IF;

		DELETE FROM monitor.simjob WHERE fileloc = floc; 
	END 
$$ LANGUAGE plpgsql;


--
-- Remove all dead and passive jobs that have been dead for more than 1 minute
--
CREATE FUNCTION monitor.cleanup_old_jobs() RETURNS void AS $$
	DECLARE
		ctime timestamp := current_timestamp;
	BEGIN
		DELETE FROM monitor.simjob 
		WHERE state='PASSIVE' and status IN('FINISHED', 'ABORTED') 
			and  (ctime-tsinstatus) > interval '1 min'; 
	END 
$$ LANGUAGE plpgsql;


--
-- Change the status of a job.
-- If the current status is FINISHED or ABORTED an error is raised
--
CREATE FUNCTION monitor.change_job_status(jid bigint, newstatus monitor.JobStatus) RETURNS void AS $$
	DECLARE
		ctime timestamp := current_timestamp;		
		oldstatus monitor.JobStatus;		
	BEGIN
		SELECT status INTO STRICT oldstatus FROM monitor.simjob WHERE jobid = jid;
		IF oldstatus IN ('FINISHED','ABORTED') THEN
			RAISE EXCEPTION  'cannot change status % of job % because the job is dead', oldstatus, jid;
		END IF;
		 
		IF oldstatus<>newstatus THEN
			UPDATE monitor.simjob 
				SET status = newstatus, last_status=oldstatus, tsinstatus=ctime, state='READY'  
				WHERE jobid = jid;
		END IF;
	END 
$$ LANGUAGE plpgsql;


--
-- Change the status of a job to new status, if the job is at the given
-- old status, else fail. If the transition requested is not legal, fail.
--
-- On failure an exception is raised. 
--
CREATE FUNCTION monitor.transition_job_status(jid bigint, oldstatus monitor.JobStatus, newstatus monitor.JobStatus) 
  RETURNS void AS 
$$
	DECLARE 
		prevstatus monitor.JobStatus;
	BEGIN
		-- Check that the caller has the right old status
		SELECT status INTO STRICT prevstatus FROM monitor.simjob WHERE jobid = jid;
		
		IF prevstatus<>oldstatus THEN
			RAISE EXCEPTION 'the previous status of % is % and not %', jid, prevstatus, oldstatus;
		END IF;
		
		-- Check that the transition is valid
		IF newstatus='INIT' OR
			(newstatus='PREPARED' and oldstatus<>'INIT') OR
			(newstatus='GENERATED' and oldstatus<>'PREPARED') OR			
			(newstatus='COMPILED' and oldstatus<>'GENERATED') OR
			(newstatus='STARTED' and oldstatus<>'COMPILED') OR
			(newstatus='FINISHED' and oldstatus<>'STARTED') OR
			(newstatus='ABORTED' and oldstatus in ('FINISHED', 'ABORTED')) THEN
			RAISE EXCEPTION 'cannot transition job % from % to %', jid, oldstatus, newstatus;
		END IF;
				
		PERFORM monitor.change_job_status(jid, newstatus);
	END 
$$ LANGUAGE plpgsql;



