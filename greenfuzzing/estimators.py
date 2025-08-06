import random
import numpy as np
from sklearn.linear_model import LinearRegression


# extrapolate the coverage rate for t0+m*t0 with the whole greybox-estimator given by the paper
# called from the coverage_rate_helper
def greybox_estimator(cov_mat, t0, m, alpha, beta):
    all_estimations = []

    # line 2 - 6: get increasing start and end index for blackbox estimator
    for i in range(1, t0 + 1):
        sa = int(i ** (1 - alpha))
        ea = i
        if sa == ea:
            continue
    
        # line 7 - 8: get all indexes from the blackbox range and shuffle them
        all_indexes = []
        for k in range(sa, ea + 1):
            all_indexes.append(k)
        random.shuffle(all_indexes)
        
        # line 9 - 14: go over increasing indexes and get singletons and doubletons for these indexes and estimate the coverage
        for j in range(1, ea - sa + 1):
            singletons, doubletons = cov_mat.get_number_singletons_doubletons_in_range(all_indexes[0:j])
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
    u = np.exp(model.predict(np.log(t0 + m * t0).reshape(-1, 1)))
    return u[0]



# an estimator for the t+1-th cycle and uses the whole coverage matrix
# called from the coverage_rate_helper
def blackbox_estimator(cov_mat, t):
    singletons, doubletons = cov_mat.get_number_singletons_doubletons()
    singletons += 1
    doubletons += 1
    estimation = (singletons / t) * (((t-1) * singletons) / ((t-1) * singletons + 2 * doubletons))
    return estimation