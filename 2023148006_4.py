# imports 2023148006_1.py (no AC) and 2023148006_2.py (AC),
# runs the simulations, shows a single overall progress bar,
# and plots mean completion time vs word length.

import argparse
import importlib.util
import random
import string
import datetime
from statistics import mean
from types import SimpleNamespace
import matplotlib.pyplot as plt


def load_module_from_path(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load module from {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def random_word(rng: random.Random, m: int) -> str:
    letters = string.ascii_lowercase
    return "".join(rng.choice(letters) for _ in range(m))


def print_bar(prefix: str, curr: int, total: int, width: int = 42, suffix: str = ""):
    frac = 0 if total == 0 else curr / total
    filled = int(frac * width)
    bar = "█" * filled + "─" * (width - filled)
    pct = f"{frac*100:6.2f}%"
    print(f"\r{prefix} [{bar}] {pct} {suffix}", end="", flush=True)


def build_args_namespace(base, target_word: str, seed: int):
    return SimpleNamespace(
        random_seed=seed,
        N=base.N,
        L=base.L,
        K=base.K,
        a=base.a,
        b=base.b,
        c=base.c,
        d=base.d,
        E=base.E,
        target_word=target_word,
    )


def main():
    ap = argparse.ArgumentParser(description="Task 4 driver")
    ap.add_argument("--no_ac_path", type=str, default="2023148006_1.py")
    ap.add_argument("--ac_path", type=str, default="2023148006_2.py")
    ap.add_argument("--min_len", type=int, default=1)
    ap.add_argument("--max_len", type=int, default=12)
    ap.add_argument("--trials", type=int, default=1000)
    ap.add_argument("--random_seed", type=int, default=datetime.datetime.now().microsecond)  # seed for driver's seed

    ap.add_argument("--N", type=int, default=4)
    ap.add_argument("--L", type=float, default=0.1)   # TA: 0.1
    ap.add_argument("--K", type=float, default=3.0)
    ap.add_argument("--a", type=float, default=0.1)
    ap.add_argument("--b", type=float, default=0.25)  # TA: 0.25
    ap.add_argument("--c", type=float, default=0.2)
    ap.add_argument("--d", type=float, default=0.15)
    ap.add_argument("--E", type=float, default=0.15)
    ap.add_argument("--outfile", type=str, default="2023148006_4.png")
    args = ap.parse_args()

    noac_mod = load_module_from_path("noac_mod", args.no_ac_path)
    ac_mod = load_module_from_path("ac_mod",   args.ac_path)

    rng = random.Random(args.random_seed)

    lengths = list(range(args.min_len, args.max_len + 1))
    means_no, means_ac = [], []

    total_steps = (args.max_len - args.min_len + 1) * args.trials * 2
    step = 0

    print(f"Params: N={args.N} L={args.L} K={args.K} a={args.a} b={args.b} c={args.c} d={args.d} E={args.E}")
    print("Running simulations…")
    print_bar("Progress:", 0, total_steps, suffix="current=")

    for m in lengths:
        times_no, times_ac = [], []
        for trial in range(args.trials):
            word = random_word(rng, m)
            # each trial has a seed that is derived from the main random seed
            # each trial's seed is a bit different
            child_seed = (args.random_seed if (args.random_seed is not None) else 0) + (m * args.trials + trial)

            noac_args = build_args_namespace(args, word, child_seed)
            ac_args = build_args_namespace(args, word, child_seed)

            t_no = noac_mod.simulate(noac_args, suppress_output=True)
            times_no.append(t_no)
            step += 1
            print_bar("Progress:", step, total_steps, suffix=f"current={m}")

            t_ac = ac_mod.simulate(ac_args, suppress_output=True)
            times_ac.append(t_ac)
            step += 1
            print_bar("Progress:", step, total_steps, suffix=f"current={m}")

        mu_no = mean(times_no)
        mu_ac = mean(times_ac)
        means_no.append(mu_no)
        means_ac.append(mu_ac)

    print()  # newline after progress bar

    # plot
    plt.figure(figsize=(8, 4.5))
    plt.plot(lengths, means_no, color="#FF0000", linewidth=2, label="No suggestions (Task 1)")
    plt.plot(lengths, means_ac, color="#0000FF", linewidth=2, label="Accept when available (Task 2)")
    plt.xlabel("Word length (chars)")
    plt.ylabel("Mean completion time (s)")
    plt.title("Task 4: Effect of error rate = 0.15")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
