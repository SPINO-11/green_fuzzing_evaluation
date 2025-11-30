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
def end_docker_trial(experiment, trial_id):
    if not experiment_utils.is_local_experiment():
        return
    name = experiment_utils.get_trial_instance_name(experiment, trial_id)
    subprocess.run(["docker", "stop", name], check=True)



# adds new cycles to the coverage matrix and compute the coverage_rates with blackbox (one-step estimator) or greybox (extrapolator) estimator and stop a trial if it not reach a certain threshold
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
        print(f"### t: {trial}, c: {cycle}, n: {len(cov_mat.all_branches)}, s: {snapshot.edges_covered}, d: {snapshot.edges_covered - len(cov_mat.all_branches)}")
        return
    
    # if its not the first cycle, it gets the entry from the Coverage_Matrix_DB, loads the coverage matrix, enters the new branches and save it again in the database
    with db_utils.session_scope() as session:
        entry = session.query(Coverage_Matrix_DB).filter_by(trial=trial, cycle=cycle-1).first()

    """
    first case saves every cycle seperately in the database while the second only stores one coverage matrix per trial
    comment out which case should be performed
    """
    #cov_mat = pickle.loads(entry.coverage_matrix)
    #cov_mat.insert_new_cycle(branches, hit_counts)
    #pickled = pickle.dumps(cov_mat)
    #entry_new = Coverage_Matrix_DB(trial=trial, cycle=cycle, coverage_matrix=pickled, all_branches=len(cov_mat.all_branches))
    #db_utils.add_all([entry, entry_new])

    cov_mat = pickle.loads(entry.coverage_matrix)
    cov_mat.insert_new_cycle(branches, hit_counts)
    pickled = pickle.dumps(cov_mat) 
    entry.coverage_matrix = pickled
    entry.cycle = cycle
    entry.all_branches = len(cov_mat.all_branches)
    db_utils.add_all([entry])

    """
    compute the coverage_rate with the estimators
    comment out if predictions should be performed
    """
    #m = 0.5
    #n = 25
    #if cycle >= 50:
    #    n = 15
    #if cycle >= 75:
    #    n = 5
    #if cycle >= 100:
    #    n = 1
    #alpha = 0.15
    #beta = 0.4
    #coverage_rate_b = estimators.blackbox_estimator(cov_mat, cycle)
    #coverage_rate_g = estimators.greybox_estimator(cov_mat, cycle, m, alpha, beta, n)
    
    #print(f"### t: {trial}, c: {cycle}, pc: {cycle + m * cycle}, b: {coverage_rate_b}, g: {coverage_rate_g}, n: {len(cov_mat.all_branches)}, s: {snapshot.edges_covered}, d: {snapshot.edges_covered - len(cov_mat.all_branches)}")
    print(f"### t: {trial}, c: {cycle}, n: {len(cov_mat.all_branches)}, s: {snapshot.edges_covered}, d: {snapshot.edges_covered - len(cov_mat.all_branches)}")

    """
    stops the trial if the coverage rate falls beneath a certain threshold
    comment out if stopping trials should be performed
    TODO: For Future work: need to implement savings of the previous predicitons from one-step estimator and extrapolator in coverage matrix or database for after-jump detection and stability-based threshold
    """
    #threshold = 0.29
    #if coverage_rate_b < threshold and coverage_rate_g < threshold:
    #    with db_utils.session_scope() as session:
    #        trial = session.query(Trial).filter_by(id=trial).first()
    #    trial.time_ended = datetime.datetime.now(datetime.timezone.utc)
    #    db_utils.add_all([trial])
    #    end_docker_trial(experiment, trial)



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
                try-except block

    
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