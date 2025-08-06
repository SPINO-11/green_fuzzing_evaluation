with open("greenfuzzing/out.txt", "r") as out:
    lines = out.readlines()

with open("greenfuzzing/filtered/outfiltered.txt", "w") as outf:
    for line in lines:
        if line.startswith("###"):
            outf.write(line)