import sqlite3
import pickle
import coverage_matrix
import estimators
import os
import sys
import re




def get_cov_mat(t, c):
    #conn = sqlite3.connect("") # CHANGE PATH !!!
    conn = sqlite3.connect("../done_experiments/bloaty_fuzz_target/experiment-data/local.db")
    #conn = sqlite3.connect('greenfuzzing/local.db')
    #conn = sqlite3.connect('experiment-data/local.db')
    cursor = conn.cursor()
    cursor.execute(f"SELECT coverage_matrix FROM coverage_matrix WHERE trial == {t} AND cycle == {c}") #WHERE trial == 1
    rows = cursor.fetchall()
    object = pickle.loads(rows[0][0])
    return object


def print_essentials(cov_mat):
    ALPHA = 0.11
    BETA = 0.5

    M = 1
    T = 15
    N = 5

    #print(cov_mat.matrix)
    #print(len(cov_mat.matrix))
    print(len(cov_mat.all_branches))
    #print(estimators.greybox_estimator(cov_mat, T, M, ALPHA, BETA, N))
    #print(estimators.blackbox_estimator(cov_mat, T))
    #print(T, T+M)


def print_number_of_branches_covered_first_cycle(cov_mat):
    counter = 0
    for i in range(len(cov_mat.matrix)):
        if cov_mat.matrix[i][0] == 1:
            counter += 1

    print(counter)



def outfiltered_with_estimators():
    ALPHA = 0.11
    BETA = 0.5

    M = 1
    N = 1
    with open("../done_experiments/bloaty_fuzz_target/outfiltered.txt", "r") as outf: # CHANGE PATH !!!
        with open("../done_experiments/bloaty_fuzz_target/outfilteredwestimators.txt", "w") as outfwe: # CHANGE PATH !!!
            for t in range(1, 26):
                cov_mat = get_cov_mat(t, 288)
                for c in range(0, 289):
                    print(t, c)
                    line = outf.readline()
                    crb = estimators.blackbox_estimator(cov_mat, c)
                    crg = estimators.greybox_estimator(cov_mat, c, M, ALPHA, BETA, N)
                    new_line = line.strip() + f", b: {crb}, g: {crg}\n"
                    outfwe.write(new_line)
                
                for i in range(5):
                    line = outf.readline()
                    outfwe.write(line)
                



project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)


cov_mat = get_cov_mat(1, 288)
#outfiltered_with_estimators()



