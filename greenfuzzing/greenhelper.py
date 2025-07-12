from common import experiment_utils
import database.utils as db_utils
from database.models import Snapshot
from database.models import Trial
from database.models import Coverage_Matrix_DB
import datetime
from experiment import scheduler
import subprocess
import pickle
import random
import numpy as np
from sklearn.linear_model import LinearRegression

ALPHA = 0
BETA = 0


class Coverage_Matrix:
    def __init__(self):
        self.matrix = []
        self.all_branches = []

    def init_first_cycle(self, branches):
        for branch in branches:
            self.all_branches.append(branch)
            self.matrix.append([1])

    def insert_new_branch(self, branch):
        self.all_branches.append(branch)
        self.matrix.append([])
        for i in range(len(self.matrix[0]) - 1):
            self.matrix[len(self.matrix) - 1].append(0)
        self.matrix[len(self.matrix) - 1].append(1)

    def insert_new_cycle(self, branches):
        for b in range(len(self.matrix)):
            self.matrix[b].append(0)
        for branch in branches:
            if not branch in self.all_branches:
                self.insert_new_branch(branch)
                continue
            self.matrix[self.all_branches.index(branch)][len(self.matrix[0]) - 1] = 1
    
    def get_number_singletons_doubletons(self):
        singletons = 0
        doubletons = 0
        for branch in self.matrix:
            added = sum(branch)
            if added == 1:
                singletons += 1
            elif added == 2:
                doubletons += 1
        return (singletons, doubletons)
    
    def get_number_singletons_doubletons_in_indexes(self, indexes):
        singletons = 0
        doubletons = 0
        for branch in self.matrix:
            counter = 0
            for i in indexes:
                if branch[i] == 1:
                    counter += 1
                if counter > 2:
                    break
            if counter == 1:
                singletons += 1
            elif counter == 2:
                doubletons += 1
        return (singletons, doubletons)
    


def blackbox_estimator(matrix, t0, m):
    all_estimations = []
    all_indexes = []
    for i in range(len(matrix.matrix[0])):
        all_indexes.append(i)
    random.shuffle(all_indexes)
    print("###shuffled all indexes", all_indexes)
    for j in range(1, len(all_indexes) + 1):
        singletons, doubletons = matrix.get_number_singletons_doubletons_in_indexes(all_indexes[0:j])
        try:
            estimation = singletons / j * (((j-1) * singletons) / ((j-1) * singletons + 2 * doubletons))
        except:
            continue
        all_estimations.append((j-1, estimation))
    print("### got all estimations", all_estimations)
    #reg_start = 0 # potentially with beta
    #reg_end = t0
    #if len(all_estimations) < reg_end:
    #    reg_end = len(all_estimations)
    u_vals = []
    t_vals = []
    for i in range(len(all_estimations)):
        print(i)
        t_vals.append(all_estimations[i][0])
        u_vals.append(all_estimations[i][1])
    log_t = np.log(t_vals).reshape(-1, 1)
    log_u = np.log(u_vals)
    print("### before model")
    model = LinearRegression()
    model.fit(log_t, log_u)
    print("### predict!!!")
    u = np.exp(model.predict(np.log(t0 + m * t0).reshape(-1, 1)))
    return u


def end_docker_trial(experiment, trial_id):
    if not experiment_utils.is_local_experiment():
        return
    name = experiment_utils.get_trial_instance_name(experiment, trial_id)
    subprocess.run(["docker", "stop", name], check=True)


def coverage_rate_helper(cycle, trial, snapshot, branches, experiment):
    if snapshot == None:
        return
    
    if cycle == 0:
        matrix = Coverage_Matrix()
        matrix.init_first_cycle(branches)
        pickled = pickle.dumps(matrix)
        entry = Coverage_Matrix_DB(trial=trial, matrix=pickled, cycle=cycle, all_branches=len(matrix.all_branches))
        db_utils.add_all([entry])
        return
    
    with db_utils.session_scope() as session:
        entry = session.query(Coverage_Matrix_DB).filter_by(trial=trial).first()
    matrix = pickle.loads(entry.matrix)
    matrix.insert_new_cycle(branches)
    pickled = pickle.dumps(matrix)
    entry.matrix = pickled
    entry.cycle = cycle
    entry.all_branches = len(matrix.all_branches)
    db_utils.add_all([entry])
    print("### before coverage rate")
    coverage_rate = blackbox_estimator(matrix, len(matrix.matrix[0]), 1)
    #if coverage_rate < 0:
    #    end_docker_trial(experiment, trial)

    print(f"###", len(matrix.all_branches))
    print(f"### coverage_rate: {coverage_rate} for point t+1*t with t: {cycle}")
    #print(matrix.matrix)

















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
            measure_manager_loop: added experiment name in config
            measure_snapshot_coverage: all returns are tuples with (None, None) or with (snapshot, branches)

        measurer_worker.py: 
            __init__: added self.experiment = config['experiment']
            measure_worker_loop: 
                call of greenhelper.measure_worker_test_should_break
                the call of measure_snapshot_coverage to tuple with used branches
    
    
    Scheduler: experiment/
        scheduler.py:
            schedule_loop: changes sleep time to 60 seconds
            schedule: call greenhelper.scheduler_end_expired_ended_trials instead of end_expired_trials
    
    
    Database: database/
        models.py:
            class Coverage_Matrix_DB added

    
    Other:
        experiment/resources:
            runner-startup-script-template.sh: added --name {{instance_name}}
"""