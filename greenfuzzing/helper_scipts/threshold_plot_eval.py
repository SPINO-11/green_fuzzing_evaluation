import re
import statistics
import matplotlib.pyplot as plt


beta_scores = []
time_savings = []
accuracies = []
cycles = []
ist = 0


def break_beta(cycle, num0, numc, num288):
    time_saved = 1 - (cycle / 288)
    accuracy = (numc - num0) / (num288 - num0)
    beta = (1 + 0.33 ** 2) * (accuracy * time_saved) / (0.33**2 * accuracy + time_saved)
    beta_scores.append(beta)
    time_savings.append(time_saved)
    accuracies.append(accuracy)
    cycles.append(cycle)



def t1_constant(data):
    THRESHOLD = 7.4#3.8
    TYPE = 2

    num288 = data[288][0]
    num0 = data[0][0]

    bb3 = data[12][1]
    bb2 = data[13][1]
    bb1 = data[14][1]

    for cycle in range(15, 289):
        b = data[cycle][1]
        if b > bb1 or b > bb2 or b > bb3:
            bb3 = bb2
            bb2 = bb1
            bb1 = b
            continue
        bb3 = bb2
        bb2 = bb1
        bb1 = b

        if data[cycle][TYPE] < THRESHOLD:
            break_beta(cycle, num0, data[cycle][0], num288)
            return
    
    break_beta(288, num0, num288, num288)



def t2_benchmark(data, benchmark):
    THRESHOLD = 0.0004#0.00035
    TYPE = 2

    branches_benchmark = [76184, 81598, 26740, 7526, 7190, 5990, 18874, 53854, 26506, 910]
    all_branches = branches_benchmark[benchmark]
    num288 = data[288][0]
    num0 = data[0][0]

    bb3 = data[12][1]
    bb2 = data[13][1]
    bb1 = data[14][1]

    for cycle in range(15, 289):
        b = data[cycle][1]
        if b > bb1 or b > bb2 or b > bb3:
            bb3 = bb2
            bb2 = bb1
            bb1 = b
            continue
        bb3 = bb2
        bb2 = bb1
        bb1 = b

        if data[cycle][TYPE] < THRESHOLD * all_branches:
            break_beta(cycle, num0, data[cycle][0], num288)
            return
    
    break_beta(288, num0, num288, num288)



def t3_branches(data):
    THRESHOLD = 0.00099 #0.0011
    TYPE = 2

    num288 = data[288][0]
    num0 = data[0][0]

    bb3 = data[12][1]
    bb2 = data[13][1]
    bb1 = data[14][1]

    for cycle in range(15, 289):
        b = data[cycle][1]
        if b > bb1 or b > bb2 or b > bb3:
            bb3 = bb2
            bb2 = bb1
            bb1 = b
            continue
        bb3 = bb2
        bb2 = bb1
        bb1 = b

        if data[cycle][TYPE] < THRESHOLD * data[cycle][0]:
            break_beta(cycle, num0, data[cycle][0], num288)
            return
        
    break_beta(288, num0, num288, num288)


def t4_changes(data):
    THRESHOLD = 0.29 #0.057
    TYPE = 2

    num288 = data[288][0]
    num0 = data[0][0]

    pb3 = data[12][TYPE]
    pb2 = data[13][TYPE]
    pb1 = data[14][TYPE]

    bb3 = data[12][1]
    bb2 = data[13][1]
    bb1 = data[14][1]

    for cycle in range(15, 289):
        b = data[cycle][1]
        if b > bb1 or b > bb2 or b > bb3:
            bb3 = bb2
            bb2 = bb1
            bb1 = b
            continue
        bb3 = bb2
        bb2 = bb1
        bb1 = b

        p = data[cycle][TYPE]
        if abs(pb1- p) < THRESHOLD and abs(pb2 - pb1) < THRESHOLD and abs(pb3 - pb2) < THRESHOLD:
            break_beta(cycle, num0, data[cycle][0], num288)
            return
        pb3 = pb2
        pb2 = pb1
        pb1 = p
    
    break_beta(288, num0, num288, num288)


def stop():
    float_re = r"(None|[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)"
    int_re = r"\d+"
    pattern = re.compile(rf"t:\s*({int_re}),\s*c:\s*({int_re}),\s*n:\s*({int_re}),\s*s:\s*({int_re}),\s*d:\s*({int_re}),\s*b:\s*({float_re}),\s*g:\s*({float_re})")
    with open("greenfuzzing/all.txt", "r") as data:
        for benchmark in range(1, 11):
            for trial in range(1, 26):
                trial_data = []
                for cycle in range(0, 289):
                    line = data.readline()
                    match = pattern.search(line)
                    n = int(match.group(3))
                    if cycle < 5:
                        trial_data.append([n,0,0])
                        continue
                    b = float(match.group(6))
                    g = float(match.group(8))
                    trial_data.append([n, b, g])
                

                for overhead in range(5):
                    data.readline()
                
                #if trial not in [21,22,23,24,25]:
                #    continue
                #if benchmark != 10:
                #    continue
                #t1_constant(trial_data)
                #t2_benchmark(trial_data, benchmark-1)
                #t3_branches(trial_data)
                t4_changes(trial_data)



def scatter():
    plt.figure(figsize=(6,5))
    plt.scatter(time_savings, accuracies)
    plt.xlim(-0.05, 1.05)
    plt.ylim(-0.05, 1.05)
    plt.xlabel("Time saving", fontsize=16)
    plt.ylabel("Accuracy", fontsize=16)
    plt.xticks(fontsize=14)
    plt.yticks(fontsize=14)
    plt.savefig("../done_experiments/libafl.png")




stop()
#scatter()

print("----- Results -----")
print(f"Beta scores ---- Average: {statistics.mean(beta_scores)} / Median: {statistics.median(beta_scores)} / Lowest: {min(beta_scores)} / Highest: {max(beta_scores)}")
print(f"Accuracy ------- Average: {statistics.mean(accuracies)} / Median: {statistics.median(accuracies)} / Lowest: {min(accuracies)} / Highest: {max(accuracies)}")
print(f"Time savings --- Average: {statistics.mean(time_savings)} / Median: {statistics.median(time_savings)} / Lowest: {min(time_savings)} / Highest: {max(time_savings)}")
print(f"Stopped cycle -- Average: {statistics.mean(cycles)} / Median: {statistics.median(cycles)} / Lowest: {min(cycles)} / Highest: {max(cycles)}")


#test = accuracies.index(min(accuracies))
#print(test)
#print(test // 25 +1, test % 25 +1)

#counter = 0
#bad = []
#for a in accuracies:
#    if a < 0.75:
#        counter += 1
#        bad.append(a)
#
#print(counter)
##bad.sort()
#
#for a in bad:
#    i = accuracies.index(a)
#    print(i // 25 +1, i % 25 +1, cycles[i])
