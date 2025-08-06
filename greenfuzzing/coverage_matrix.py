# Class which consists of a coverage matrix 
class Coverage_Matrix:
    def __init__(self):
        self.matrix = []
        self.all_branches = []

    # insert the branches for the very first cycle
    # called from outside
    def init_first_cycle(self, branches):
        for branch in branches:
            self.all_branches.append(branch)
            self.matrix.append([1])

    # insert a branch which is not already in the coverage matrix
    # called from insert_new_cycle
    def insert_new_branch(self, branch):
        self.all_branches.append(branch)
        self.matrix.append([])
        for i in range(len(self.matrix[0]) - 1):
            self.matrix[len(self.matrix) - 1].append(0)
        self.matrix[len(self.matrix) - 1].append(1)

    # insert the branches of a cycle which is not the first one
    # called from outside
    def insert_new_cycle(self, branches):
        for b in range(len(self.matrix)):
            self.matrix[b].append(0)
        for branch in branches:
            if not branch in self.all_branches:
                self.insert_new_branch(branch)
                continue
            self.matrix[self.all_branches.index(branch)][len(self.matrix[0]) - 1] = 1
    
    # compute and return the number of singletons and doubletons in the whole coverage matrix
    # called from the outside
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
    
    # compute and return the number of singletons and doubletons in ranch which is given through a list of all indexes in the range
    # called from the outside
    def get_number_singletons_doubletons_in_range(self, indexes):
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