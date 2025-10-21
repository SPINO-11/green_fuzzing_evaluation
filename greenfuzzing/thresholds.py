import sqlite3
import pickle
import numpy as np
import random
from sklearn.linear_model import LinearRegression
import os
import sys


PATH = "../done_experiments/zlib_zlib_uncompress_fuzzer/experiment-data/local.db" # CHANGE PATH !!!
MAX_BRANCH_BENCHMARK = 76184


def get_cov_mat(t, c):
    conn = sqlite3.connect(PATH)
    cursor = conn.cursor()
    cursor.execute(f"SELECT coverage_matrix FROM coverage_matrix WHERE trial == {t} AND cycle == {c}")
    rows = cursor.fetchall()
    object = pickle.loads(rows[0][0])
    return object



def single_double(mat, indexes):
    sub = mat[:, indexes]
    sums = sub.sum(axis=1)
    singletons = np.count_nonzero(sums == 1)
    doubletons = np.count_nonzero(sums == 2)
    return int(singletons), int(doubletons)



def greybox_estimator_test(mat, t0, m):
    ALPHA = 0.11
    BETA = 0.5
    N = 1

    all_estimations = []

    # line 2 - 6: get increasing start and end index for blackbox estimator
    for i in range(1, t0 + 1):
        sa = int(i ** (1 - ALPHA))
        ea = i
        if sa == ea:
            continue

        # shuffle more times to get more estimates and cancel the shuffle bias
        for _ in range(N):
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
    sb = int(t0 ** (1 - BETA))
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
    u = np.exp(model.predict(np.log(m*t0).reshape(-1, 1))) # or t0 + m * t0
    return u[0]



def blackbox_estimator_test(mat, t):
    if t < 2:
        return None
    singletons, doubletons = single_double(mat, list(range(0, t + 1)))
    singletons += 1
    doubletons += 1
    estimation = (singletons / t) * (((t-1) * singletons) / ((t-1) * singletons + 2 * doubletons))
    return estimation



def mat_to_np(cov_mat):
    new_mat = np.zeros((len(cov_mat.matrix), len(cov_mat.matrix[0])), dtype=bool)
    for row in range(0, len(cov_mat.matrix)):
        for col in range(0, len(cov_mat.matrix[row])):
            if cov_mat.matrix[row][col] == 1:
                new_mat[row][col] = 1
    return new_mat



def get_branch_number(mat, n):
    sub = mat[:, :n+1]
    mask = np.any(sub == 1, axis=1)
    count = np.sum(mask)
    return count



def break_print(c, num0, numc, numa, s):
    t = 1 - (c / 288)
    r =  (numc - num0) / (numa - num0)
    e1 = t / (1 - r)
    e2 = (1 - r) / t
    mul = t * r
    beta = (2 * t * r) / (t + r)
    print(f"### BREAK with {s} and t: {t}, r: {r}, e1: {e1}, e2: {e2}, mul: {mul}, beta: {beta}")


def extract_thresholds_for_one_trial(t):
    cov_mat = get_cov_mat(t, 288)
    mat = mat_to_np(cov_mat)

    bb3 = 100
    bb2 = 100
    bb1 = 100

    counter = 0

    all_branches_percent = 0.0001
    branches_percent = 0.001

    tb1 = False
    tb15 = False
    tga = False
    tgn = False

    num0 = get_branch_number(mat, 0)
    numa = len(cov_mat.all_branches)

    for c in range(15, 289):
        b = blackbox_estimator_test(mat, c)
        g = greybox_estimator_test(mat, c, 1.5)
        print(f"c: {c}, blackbox: {b}, greybox: {g}")


        if b > bb1 or b > bb2 or b > bb3:
            bb3 = bb2
            bb2 = bb1
            bb1 = b
            continue
        bb3 = bb2
        bb2 = bb1
        bb1 = b

        numc = get_branch_number(mat, c)

        if b < 1 and tb1 == False:
            tb1 = True
            break_print(c, num0, numc, numa, "blackbox threshold 1")
        
        if b < 1.5 and tb15 == False:
            tb15 = True
            break_print(c, num0, numc, numa, "blackbox threshold 1.5")

        if g < all_branches_percent * MAX_BRANCH_BENCHMARK and tga == False:
            tga = True
            break_print(c, num0, numc, numa, "greybox threshold all_branches percent")

        if g < branches_percent * numc and tgn == False:
            tgn = True
            break_print(c, num0, numc, numa, "greybox threshold current_branches percent")
        

        if tb1 == True and tb15 == True and tga == True and tgn == True:
            break

"""
Zeitersparnis: t = 1 - (c / 288)
Genauigkeit: r =  (n_cycle_c - n_cycle_0) / (n_cycle_288 - n_cycle_0)
e1 = t / (1 - r) --> wie viel prozent Zeiterspranis pro Prozent Coverage Verlust --> je höher desto besser
e2 = (1 - r) / t --> wie viel prozent coverage verliere ich pro Prozent Zeitersparnis --> je kleiner desto besser
mul = t * r --> multiplikativer score --> je größer desto besser
beta = (1 + beta**2) * (t*r / (beta**2 * t + r)) --> je größer desto besser
"""




def outfiltered_with_estimators():
    with open("../done_experiments/zlib_zlib_uncompress_fuzzer/outfiltered.txt", "r") as outf: # CHANGE PATH !!!
        with open("../done_experiments/zlib_zlib_uncompress_fuzzer/outfilteredwestimators.txt", "w") as outfwe: # CHANGE PATH !!!
            for t in range(1, 26):
                cov_mat = get_cov_mat(t, 288)
                mat = mat_to_np(cov_mat)
                for c in range(0, 289):
                    print(t, c)
                    line = outf.readline()
                    crb = blackbox_estimator_test(mat, c)
                    crg = greybox_estimator_test(mat, c, 1.5)
                    new_line = line.strip() + f", b: {crb}, g: {crg}\n"
                    outfwe.write(new_line)
                
                for i in range(5):
                    line = outf.readline()
                    outfwe.write(line)



project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

#extract_thresholds_for_one_trial(1)

outfiltered_with_estimators()







"""
Possible Thresholds:
Blackbox Estimator:
    Not breaking if the coverage rate is bigger than one of the three before
    Break if the coverage rate falls under 1 or 1.5 new branches per cycle maybe also only if the three before also falls under


Greybox Estimator:
    Break under 5 or 7.5 similar of blackbox with 1 or 1.5
    Break if all_branches under 0.0001 * All_Branches
    Break if num_branches under 0.001 * num_branches
"""