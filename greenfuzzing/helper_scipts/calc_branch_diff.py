b = []
d = []


with open("branch_differences.txt", "r") as f:
    data = f.readlines()



for line in data:
    if line == "\n":
        continue
    stripped = line.split()
    b.append(int(stripped[0]))
    d.append(int(stripped[1]))


bs = 0
ds = 0
for i in range(250):
    bs += b[i]
    ds += d[i]

bsa = bs / 250
dsa = ds / 250

bso = sorted(b)
dso = sorted(d)

bsm = bso[250//2]
dsm = dso[250//2]

print(f"all branches sum: {bs}, all difference sum: {ds}, procent: {ds / bs}")
print(f"all branch avg: {bsa}, all difference avg: {dsa}, percent: {dsa / bsa}")
print(f"all branch med: {bsm}, all difference med: {dsm}, percent: {dsm / bsm}")
