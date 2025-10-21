import sqlite3
import pickle
import coverage_matrix
import estimators
import os
import sys
import re
import time
import random
import numpy as np
from sklearn.linear_model import LinearRegression







def get_cov_mat(t, c):
    #conn = sqlite3.connect("") # CHANGE PATH !!!
    conn = sqlite3.connect("greenfuzzing/local.db")
    #conn = sqlite3.connect('greenfuzzing/local.db')
    #conn = sqlite3.connect('experiment-data/local.db')
    cursor = conn.cursor()
    cursor.execute(f"SELECT coverage_matrix FROM coverage_matrix WHERE trial == 1 AND cycle == 288") #WHERE trial == 1
    rows = cursor.fetchall()
    object = pickle.loads(rows[0][0])
    return object



def single_double(mat, indexes):
    sub = mat[:, indexes]
    sums = sub.sum(axis=1)
    singletons = np.count_nonzero(sums == 1)
    doubletons = np.count_nonzero(sums == 2)
    return int(singletons), int(doubletons)



def greybox_estimator_test(mat, t0, m, alpha, beta, n):
    all_estimations = []

    # line 2 - 6: get increasing start and end index for blackbox estimator
    for i in range(1, t0 + 1):
        sa = int(i ** (1 - alpha))
        ea = i
        if sa == ea:
            continue

        # shuffle more times to get more estimates and cancel the shuffle bias
        for _ in range(n):
            # get all indexes from the blackbox range
            all_indexes = list(range(sa, ea + 1))
            random.shuffle(all_indexes)

            # line 9 - 14: go over increasing indexes and get singletons and doubletons for these indexes and estimate the coverage
            for j in range(2, ea - sa + 1):
                singletons, doubletons = single_double(mat, all_indexes[0:j])
                singletons += 1
                doubletons += 1
                estimation = (singletons / j) * (((j-1) * singletons) / ((j-1) * singletons + 2 * doubletons))
                all_estimations.append((sa + j - 1, estimation))
    
    # line 15 - 19: get start and end regression points and get extrapolation with linear regression
    sb = int(t0 ** (1 - beta))
    eb = t0
    time_vals = []
    estimation_vals = []
    for k in range(len(all_estimations)):
        if all_estimations[k][0] >= sb and all_estimations[k][0] <= eb:
            time_vals.append(all_estimations[k][0])
            estimation_vals.append(all_estimations[k][1])
    if len(time_vals) < 2:
        return None
    log_time = np.log(time_vals).reshape(-1, 1)
    log_estimation = np.log(estimation_vals)
    model = LinearRegression()
    model.fit(log_time, log_estimation)
    u = np.exp(model.predict(np.log(t0 + m).reshape(-1, 1))) # or t0 + m * t0
    return u[0]






project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

cov_mat = get_cov_mat(1, 288)
print("start")
#start1 = time.time()
#u = estimators.greybox_estimator(cov_mat, 288, 1, 0.11, 0.5, 1)
#end1 = time.time()
#print(f"u: {u}, time: {end1 - start1}")


start2 = time.time()
new_mat = np.zeros((len(cov_mat.matrix), len(cov_mat.matrix[0])), dtype=bool)
for row in range(0, len(cov_mat.matrix)):
    for col in range(0, len(cov_mat.matrix[row])):
        #new_mat[row][col] = cov_mat.matrix[row][col]
        if cov_mat.matrix[row][col] == 1:
            new_mat[row][col] = 1
end2 = time.time()
print(f"time: {end2 - start2}")


start3 = time.time()
u2 = greybox_estimator_test(new_mat, 288, 1, 0.11, 0.5, 1)
end3 = time.time()
print(f"u: {u2}, time: {end3 - start3}")
print("stop")