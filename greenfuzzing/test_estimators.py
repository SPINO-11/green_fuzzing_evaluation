import sqlite3
import pickle
import coverage_matrix
import estimators
import os
import sys



ALPHA = 0.11
BETA = 0.5

TRIAL = 0
M = 1
T = 0



def get_cov_mat():
    conn = sqlite3.connect('greenfuzzing/local.db')
    cursor = conn.cursor()
    cursor.execute("SELECT coverage_matrix FROM coverage_matrix") #WHERE trial == 1
    rows = cursor.fetchall()
    object = pickle.loads(rows[0][0])
    return object


project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)


cov_mat = get_cov_mat()
u = estimators.greybox_estimator(cov_mat, T, M, ALPHA, BETA)

print(u)