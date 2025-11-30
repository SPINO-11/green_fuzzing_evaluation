with open("../done_experiments/openssl_x509/out.txt", "r") as out: # CHANGE PATH !!!
    lines = out.readlines()

with open("../done_experiments/openssl_x509/outfiltered.txt", "w") as outf: # CHANGE PATH !!!
    for i in range(1, 26):
        for line in lines:
            if line.startswith(f"### t: {i},"):
                outf.write(line)
        outf.write("\n\n!\n\n\n")

    #for line in lines:
    #    if line.startswith("### "):
    #        outf.write(line)
