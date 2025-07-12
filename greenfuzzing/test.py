import test2
import random
import numpy as np
from sklearn.linear_model import LinearRegression

matrizes = {}


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




t1 = Coverage_Matrix()
matrizes[str(1)] = t1

matrizes[str(1)].init_first_cycle([[2], [4], [7], [1]])

matrizes[str(1)].insert_new_cycle([[2], [5], [1], [3]])

matrizes[str(1)].insert_new_cycle([[5], [7], [1], [9]])

print(matrizes[str(1)].matrix)
print(matrizes[str(1)].all_branches)


def blackbox_estimator(matrix):
    all_estimations = []
    all_indexes = []
    for i in range(len(matrix.matrix[0])):
        all_indexes.append(i)
    print(all_indexes)
    random.shuffle(all_indexes)
    print(all_indexes)
    for j in range(1, len(all_indexes) + 1):
        print()
        print(all_indexes[0:j])
        singletons, doubletons = matrix.get_number_singletons_doubletons_in_indexes(all_indexes[0:j])
        print(singletons, doubletons)
        try:
            estimation = singletons / j * (((j-1) * singletons) / ((j-1) * singletons + 2 * doubletons))
        except:
            continue
        all_estimations.append((j-1, estimation))
    print(all_estimations)
    return 0

print()
blackbox_estimator(matrizes[str(1)])




print()
print()
print()

model = LinearRegression()
model.fit([[1], [2], [3]], [2, 4, 6])

u = model.predict([[4]])
print(u)

#test2.t("a")
#test2.t("b")