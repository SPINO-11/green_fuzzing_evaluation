# Class which consists of a coverage matrix 
class Coverage_Matrix:
    def __init__(self):
        self.matrix = []
        self.all_branches = []
        self.all_hit_counts = []
        self.cycle = 0


    # insert the branches for the very first cycle
    # called from outside
    def init_first_cycle(self, branches, hit_counts):
        for i in range(len(branches)):
            self.all_branches.append(branches[i])
            self.all_hit_counts.append(hit_counts[i])
            self.matrix.append([1])


    # insert a branch which is not already in the coverage matrix
    # called from insert_new_cycle
    def insert_new_branch(self, branch, hit_count):
        num_all_branches = len(self.all_branches)

        self.all_branches.append(branch)
        self.all_hit_counts.append(hit_count)
        self.matrix.append([])

        for i in range(self.cycle):
            self.matrix[num_all_branches].append(0)

        self.matrix[num_all_branches].append(1)


    # insert the branches of a cycle which is not the first one
    # called from outside
    def insert_new_cycle(self, branches, hit_counts):
        self.cycle += 1

        # coverage error occured so it gets filled with zeros
        if branches == []:
            for i in range(len(self.all_branches)):
                self.matrix[i].append(0)
            return

        # in the first cycle occured a coverage error
        if self.matrix == []:
            for i in range(len(branches)):
                self.matrix.append([])
                self.all_branches.append(branches[i])
                self.all_hit_counts.append(0)
                # append so many 0s because it can be multiple errors after an error in the first cycle
                for j in range(self.cycle):
                    self.matrix[i].append(0)

        # insert the correct cycle
        for b in range(len(self.all_branches)):
            self.matrix[b].append(0)

        for i in range(len(branches)):
            if not branches[i] in self.all_branches:
                self.insert_new_branch(branches[i], hit_counts[i])
                continue
            idx = self.all_branches.index(branches[i])
            if hit_counts[i] > self.all_hit_counts[idx]:
                self.matrix[idx][self.cycle] = 1
                self.all_hit_counts[idx] = hit_counts[i]


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
    