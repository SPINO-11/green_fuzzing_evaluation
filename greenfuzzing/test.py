import json

def get_covered_branches_from_summary_json(summary_json_file):
    covered_branches = []
    covered_hit_counts = []
    try:
        coverage_info = summary_json_file
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

        test = []
        functions_datas = coverage_info['data'][0]['files']
        for function_data in functions_datas:
            for branch in function_data['branches']:
                if branch[type_index] == branch_region_type:
                    if branch[hit_true_index] > 0:
                        b = branch[:hit_true_index] + branch[file_index:] + [1] # 1 is true path
                        if b not in test:
                            test.append(b)
                            
                    if branch[hit_false_index] > 0:
                        b = branch[:hit_true_index] + branch[file_index:] + [0] # 0 is false path
                        if b not in test:
                            test.append(b)#
                    
        print(f"files covered: {len(test)}")

    except Exception:  # pylint: disable=broad-except
        print('Coverage summary json file defective or missing.')
    return covered_branches, covered_hit_counts





with open("greenfuzzing/coverage-archive-0000.json", "r") as f:
    data = json.load(f)

summary = data['data'][0]['totals']['branches']['covered']
print(f"covered totals: {summary}")

print(data['data'][0].keys())

got = get_covered_branches_from_summary_json(data)
print(f"branches covered: {len(got[0])}")


