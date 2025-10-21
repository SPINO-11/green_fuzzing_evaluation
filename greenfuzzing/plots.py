import re
import matplotlib.pyplot as plt



def plot_all_trials_seperately():
    filename = "../done_experiments/openssl_x509/outfiltered.txt"  # CHANGE PATH !!!
    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()

    data = {}
    pattern = re.compile(r"t:\s*(\d+),\s*c:\s*(\d+),\s*n:\s*(\d+)")
    for line in lines:
        match = pattern.search(line)
        if match:
            t = int(match.group(1))
            c = int(match.group(2))
            n = int(match.group(3))
            data.setdefault(t, []).append((c, n))
    
    for t, points in data.items():
        x_vals = [p[0] for p in points]
        y_vals = [p[1] for p in points]

        plt.figure(figsize=(8, 5))
        plt.plot(x_vals, y_vals, '-o', markersize=3, label=f"t = {t}")
        plt.title(f"Plot for t = {t}")
        plt.xlabel("measure points")
        plt.ylabel("covered branches")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()

        plt.savefig(f"../done_experiments/openssl_x509/plots/all_trials_seperately/plot{t}.png", dpi=200) # save plots: CHANGE PATH !!!
        plt.close()




plot_all_trials_seperately()