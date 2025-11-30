import re
import matplotlib.pyplot as plt


PATH = "openssl_x509"


def plot_all_trials_seperately():
    filename = f"../done_experiments/{PATH}/outfiltered.txt"  # CHANGE PATH !!!
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
        if t != 13:
            continue
        x_vals = [p[0] for p in points]
        y_vals = [p[1] for p in points]

        plt.figure(figsize=(8, 5))
        plt.plot(x_vals, y_vals, '-o', markersize=5, linewidth=3.5, label=f"coverage curve")
        plt.xlabel("Measurement cycles", fontsize=16)
        plt.ylabel("Covered branches", fontsize=16)
        plt.xticks(fontsize=14)
        plt.yticks(fontsize=14)
        plt.grid(True)
        plt.legend(fontsize=14)
        plt.tight_layout()

        plt.savefig(f"../done_experiments/bloaty{t}.png", dpi=200) # save plots: CHANGE PATH !!!
        plt.close()



def plot_all_trials_blackbox():
    filename = f"../done_experiments/{PATH}/outfilteredwestimators.txt"  # CHANGE PATH !!!
    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()

    data = {}
    #pattern = re.compile(r"t:\s*(\d+),\s*c:\s*(\d+),\s*n:\s*(\d+),\s*s:\s*(\d+),\s*d:\s*(\d+),\s*b:\s*(\d+),\s*g:\s*(\d+)")
    float_re = r"(None|[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)"
    int_re = r"\d+"
    pattern = re.compile(rf"t:\s*({int_re}),\s*c:\s*({int_re}),\s*n:\s*({int_re}),\s*s:\s*({int_re}),\s*d:\s*({int_re}),\s*b:\s*({float_re}),\s*g:\s*({float_re})")

    for line in lines:
        match = pattern.search(line)
        if match:
            t = int(match.group(1))
            c = int(match.group(2))
            n = int(match.group(3))
            if c >= 15:
                b = float(match.group(6))
            else:
                b = 0
            data.setdefault(t, []).append((c, n, b))

    for t, points in data.items():
        if t != 3:
            continue
        x_vals = [p[0] for p in points]  # c
        n_vals = [p[1] for p in points]  # n
        b_vals = [p[2] for p in points]  # b

        fig, ax1 = plt.subplots(figsize=(8, 5))

        # Linke y-Achse: n
        ax1.plot(x_vals, n_vals, '-o', markersize=5, linewidth=3.5, color='tab:blue', label='coverage curve')
        ax1.set_xlabel("Measurement cycles", fontsize=16)
        ax1.set_ylabel("Covered branches", fontsize=16, color='tab:blue')
        ax1.tick_params(axis='y', labelcolor='tab:blue')
        ax1.grid(True)

        # Rechte y-Achse: b
        ax2 = ax1.twinx()
        x_b = [x for x in x_vals if x >= 15]
        b_b = [b for (x, b) in zip(x_vals, b_vals) if x >= 15]
        ax2.plot(x_b, b_b, '-s', markersize=5, linewidth=3.5, color='tab:red', label='one-step estimation curve')
        ax2.set_ylabel("One-step estimator predictions", fontsize=16, color='tab:red')
        ax2.tick_params(axis='y', labelcolor='tab:red')

        lines_1, labels_1 = ax1.get_legend_handles_labels()
        lines_2, labels_2 = ax2.get_legend_handles_labels()
        ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='center right')

        # Titel + Layout
        #plt.title(f"Plot for t = {t}")
        plt.xticks(fontsize=14)
        plt.yticks(fontsize=14)
        plt.tight_layout()
        
        plt.savefig(f"../done_experiments/black_typical.png", dpi=200)
        plt.close()
    



def plot_all_trials_greybox():
    filename = f"../done_experiments/{PATH}/outfilteredwestimators.txt"  # CHANGE PATH !!!
    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()

    data = {}
    #pattern = re.compile(r"t:\s*(\d+),\s*c:\s*(\d+),\s*n:\s*(\d+),\s*s:\s*(\d+),\s*d:\s*(\d+),\s*b:\s*(\d+),\s*g:\s*(\d+)")
    float_re = r"(None|[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)"
    int_re = r"\d+"
    pattern = re.compile(rf"t:\s*({int_re}),\s*c:\s*({int_re}),\s*n:\s*({int_re}),\s*s:\s*({int_re}),\s*d:\s*({int_re}),\s*b:\s*({float_re}),\s*g:\s*({float_re})")

    for line in lines:
        match = pattern.search(line)
        if match:
            t = int(match.group(1))
            c = int(match.group(2))
            n = int(match.group(3))
            if c >= 15:
                b = float(match.group(8))
            else:
                b = 0
            data.setdefault(t, []).append((c, n, b))

    for t, points in data.items():
        if t != 17:
            continue
        x_vals = [p[0] for p in points]  # c
        n_vals = [p[1] for p in points]  # n
        b_vals = [p[2] for p in points]  # b

        fig, ax1 = plt.subplots(figsize=(8, 5))

        # Linke y-Achse: n
        ax1.plot(x_vals, n_vals, '-o', markersize=5, linewidth=3.5, color='tab:blue', label='coverage curve')
        ax1.set_xlabel("Measurement cycles", fontsize=16)
        ax1.set_ylabel("Covered branches", fontsize=16, color='tab:blue')
        ax1.tick_params(axis='y', labelcolor='tab:blue')
        ax1.grid(True)

        # Rechte y-Achse: b
        ax2 = ax1.twinx()
        x_b = [x for x in x_vals if x >= 15]
        b_b = [b for (x, b) in zip(x_vals, b_vals) if x >= 15]
        ax2.plot(x_b, b_b, '-s', markersize=5, linewidth=3.5, color='tab:red', label='extrapolation curve')
        ax2.set_ylabel("Extrapolator predictions", fontsize=16, color='tab:red')
        ax2.tick_params(axis='y', labelcolor='tab:red')

        ax1.axvline(x=150, color='black', linestyle='--', linewidth=3.5, label='stopped cycle (150)')

        lines_1, labels_1 = ax1.get_legend_handles_labels()
        lines_2, labels_2 = ax2.get_legend_handles_labels()
        ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='center right')

        # Titel + Layout
        #plt.title(f"Plot for t = {t}")
        plt.xticks(fontsize=14)
        plt.yticks(fontsize=14)
        plt.tight_layout()
        
        plt.savefig(f"../done_experiments/instability_openssl_2.png", dpi=200)
        plt.close()



#plot_all_trials_seperately()
#plot_all_trials_blackbox()
plot_all_trials_greybox()
