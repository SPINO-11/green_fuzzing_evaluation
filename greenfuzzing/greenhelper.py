from common import experiment_utils
import database.utils as db_utils
from database.models import Snapshot
from database.models import Trial
import datetime
from experiment import scheduler
import subprocess



def end_docker_trial(experiment, trial_id, logger):
    if not experiment_utils.is_local_experiment():
        return
    name = experiment_utils.get_trial_instance_name(experiment, trial_id)
    subprocess.run(["docker", "stop", name], check=True)


# used in experiment/measurer/measure_worker.py/measure_worker_loop(self)
def measure_worker_test_should_break(measured_snapshot, request, logger, experiment):
    #print(f"############# trial: {request.trial_id}, cycle: {request.cycle}, snapshot: {measured_snapshot}")
    if measured_snapshot == None or request.cycle == 0 or request.cycle == 1:
        print(f"im in and none or to early, trial: {request.trial_id}")
        return False
 
    time_before = experiment_utils.get_cycle_time(request.cycle - 1)
    time_2before = experiment_utils.get_cycle_time(request.cycle - 2)
    with db_utils.session_scope() as session:
        snapshot_before = session.query(Snapshot).filter_by(time=time_before, trial_id=request.trial_id).first()
        snapshot_2before = session.query(Snapshot).filter_by(time=time_2before, trial_id=request.trial_id).first()
    coverage_now = measured_snapshot.edges_covered
    coverage_before = snapshot_before.edges_covered
    coverage_2before = snapshot_2before.edges_covered
    coverage_diff = coverage_now - coverage_before
    coverage_diff_before = coverage_before - coverage_2before

    if coverage_diff < coverage_diff_before // 2:
    #if request.trial_id != 8 or request.cycle == 4:
        with db_utils.session_scope() as session:
            trial = session.query(Trial).filter_by(id=request.trial_id).first()
        trial.time_ended = datetime.datetime.now(datetime.timezone.utc)
        db_utils.add_all([trial])
        end_docker_trial(experiment, request.trial_id,  logger)
        return True
    
    return False


















# used in experiment/scheduler.py/schedule(experiment_config, pool, core_allocation)
def scheduler_end_expired_ended_trials(experiment_config, core_allocation, logger):
    """Get all expired trials, end them and return them."""
    trials_past_expiry = scheduler.get_expired_trials(experiment_config['experiment'], experiment_config['max_total_time'])
    trials_manually_ended = scheduler.get_nonpreempted_trials(experiment_config['experiment']).filter(Trial.time_ended.isnot(None))
    all_trials_that_should_end = list(trials_past_expiry) + list(trials_manually_ended)

    if not all_trials_that_should_end:
        return
    
    expired_instances = []
    expired_trial_ids = []
    current_dt = scheduler.datetime_now()

    for trial in all_trials_that_should_end:
        trial_id = trial.id
        if trial.time_ended is None:
            trial.time_ended = current_dt
        expired_instances.append(experiment_utils.get_trial_instance_name(experiment_config['experiment'], trial_id))
        expired_trial_ids.append(trial_id)

    # Bail out here because trials_past_expiry will be truthy until evaluated.
    if not expired_instances:
        return

    if core_allocation is not None:
        for cpuset, trial_id in core_allocation.items():
            if trial_id in expired_trial_ids:
                core_allocation[cpuset] = None

    if not experiment_utils.is_local_experiment() and not scheduler.delete_instances(expired_instances, experiment_config):
        # If we failed to delete some instances, then don't update the status
        # of expired trials in database as we don't know which instances were
        # successfully deleted. Wait for next iteration of end_expired_trials.
        logger.error('Failed to delete instances after trial expiry.')
        return

    db_utils.bulk_save(all_trials_that_should_end)











"""
Any changes:
    Measurer: experiment/measurer/
        measurer_manager.py: 
            measure_manager_loop: added experiment name in config

        measurer_worker.py: 
            __init__: added self.experiment = config['experiment']
            measure_worker_loop: call of greenhelper.measure_worker_test_should_break
    
    
    Scheduler: experiment/
        scheduler.py:
            schedule_loop: changes sleep time to 60 seconds
            schedule: call greenhelper.scheduler_end_expired_ended_trials instead of end_expired_trials
    
    
    Other:
        experiment/resources:
            runner-startup-script-template.sh: added --name {{instance_name}}
"""