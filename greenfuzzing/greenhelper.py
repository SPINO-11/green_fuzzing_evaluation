from common import experiment_utils
import database.utils as db_utils
from database.models import Snapshot
from database.models import Trial
from database.models import Coverage_Matrix_DB
import datetime
from experiment import scheduler
import subprocess
import pickle
from greenfuzzing import coverage_matrix
from greenfuzzing import estimators
from experiment.measurer import coverage_utils



# stops the docker of a particular trial to stop the experiment further
# called from the coverage_rate_helper
def end_docker_trial(experiment, trial_id):
    if not experiment_utils.is_local_experiment():
        return
    name = experiment_utils.get_trial_instance_name(experiment, trial_id)
    subprocess.run(["docker", "stop", name], check=True)



# adds new cycles to the coverage matrix and compute the coverage_rates with blackbox or greybox estimator and stop a trial if it not reach a certain threshold
# called from experiment/measurer/measure_worker.py in measure_worker_loop()
def coverage_rate_helper(cycle, trial, snapshot, branches, hit_counts, experiment):
    # if there are no data nothing to be done
    if snapshot == None:
        return
    
    # if its the first cycle, create new Coverage_Matrix object fill it with the branches and save it in the Coverage_Matrix_DB
    if cycle == 0:
        cov_mat = coverage_matrix.Coverage_Matrix()
        cov_mat.init_first_cycle(branches, hit_counts)
        pickled = pickle.dumps(cov_mat)
        entry = Coverage_Matrix_DB(trial=trial, cycle=cycle, coverage_matrix=pickled, all_branches=len(cov_mat.all_branches))
        db_utils.add_all([entry])
        return
    
    # if its not the first cycle, it gets the entry from the Coverage_Matrix_DB, loads the coverage matrix, enters the new branches and save it again in the database
    with db_utils.session_scope() as session:
        entry = session.query(Coverage_Matrix_DB).filter_by(trial=trial, cycle=cycle-1).first()
    cov_mat = pickle.loads(entry.coverage_matrix)
    cov_mat.insert_new_cycle(branches, hit_counts)
    pickled = pickle.dumps(cov_mat)
    entry_new = Coverage_Matrix_DB(trial=trial, cycle=cycle, coverage_matrix=pickled, all_branches=len(cov_mat.all_branches))
    db_utils.add_all([entry, entry_new])

    # compute the coverage_rate with the estimators
    m = 0.5
    n = 5
    alpha = 0.11
    beta = 0.5
    coverage_rate_b = estimators.blackbox_estimator(cov_mat, cycle)
    coverage_rate_g = estimators.greybox_estimator(cov_mat, cycle, m, alpha, beta, n)
    
    print(f"### t: {trial}, c: {cycle}, pc: {cycle + m * cycle}, b: {coverage_rate_b}, g: {coverage_rate_g}, n: {len(cov_mat.all_branches)}, s: {snapshot.edges_covered}, d: {snapshot.edges_covered - len(cov_mat.all_branches)}")

#    # stops the trial if the coverage rate falls beneath a certain threshold
#    if coverage_rate_b < 0 and coverage_rate_g < 0:
#        with db_utils.session_scope() as session:
#            trial = session.query(Trial).filter_by(id=trial).first()
#        trial.time_ended = datetime.datetime.now(datetime.timezone.utc)
#        db_utils.add_all([trial])
#        end_docker_trial(experiment, trial)



# extracts all branches from the coverage summary json with distinkt true and false paths
# called from experiment/measurer/measure_manager.py in measure_snapshot_coverage(...)
def get_covered_branches_from_summary_json(summary_json_file):
    covered_branches = []
    covered_hit_counts = []
    try:
        coverage_info = coverage_utils.get_coverage_infomation(summary_json_file)
        functions_data = coverage_info['data'][0]['functions']

        hit_true_index = 4
        hit_false_index = 5
        type_index = -1
        branch_region_type = 4
        file_index = 6

        for function_data in functions_data:
            for branch in function_data['branches']:
                if branch[type_index] == branch_region_type:
                    if branch[hit_true_index] > 0:
                        b = branch[:hit_true_index] + branch[file_index:] + [1] # 1 is true path
                        if b not in covered_branches:
                            covered_branches.append(b)
                            covered_hit_counts.append(branch[hit_true_index])
                    if branch[hit_false_index] > 0:
                        b = branch[:hit_true_index] + branch[file_index:] + [0] # 0 is false path
                        if b not in covered_branches:
                            covered_branches.append(b)
                            covered_hit_counts.append(branch[hit_false_index])

    except Exception:  # pylint: disable=broad-except
        print('Coverage summary json file defective or missing.')
    return covered_branches, covered_hit_counts
    








##################################################################################################################################

# used in experiment/measurer/measure_worker.py/measure_worker_loop(self)
def measure_worker_test_should_break(measured_snapshot, request, experiment):
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
        end_docker_trial(experiment, request.trial_id)
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
            measure_manager_loop: 
                added experiment name in config
            measure_snapshot_coverage: 
                all returns are tuples with (None, None, None) or with (snapshot, branches, hit_counts) 
                branches, hit_counts are get from greenhelper get_covered_branches_from_summary_json

        measurer_worker.py: 
            __init__: added self.experiment = config['experiment']
            measure_worker_loop: 
                call of greenhelper.coverage_rate_helper
                the call of measure_snapshot_coverage to tripple with used branches and hit_counts
    
    
    Scheduler: experiment/
        scheduler.py:
            schedule_loop: changes sleep time to 60 seconds
            schedule: call greenhelper.scheduler_end_expired_ended_trials instead of end_expired_trials

    
    Runner: experiment/
        runner.py:
            archive_corpus:
                retry to make the tarfile if it is corrputed until it is not corrupted anymore
    
    
    Database: database/
        models.py:
            class Coverage_Matrix_DB added

    
    Other:
        experiment/resources:
            runner-startup-script-template.sh: added --name {{instance_name}}
"""