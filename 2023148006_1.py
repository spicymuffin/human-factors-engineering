import numpy as np
import argparse

# MHP
TAU_P = 0.10
TAU_C = 0.07

parser = argparse.ArgumentParser(description="Typing simulation")

parser.add_argument("--random_seed", type=int, default=None)
parser.add_argument("--N", type=int, default=4)  # number of suggested words
parser.add_argument("--L", type=float, default=0.3)  # word suggestion latency L
parser.add_argument("--K", type=float, default=3)  # fitts law ID
parser.add_argument("--a", type=float, default=0.1)  # fitts law param a
parser.add_argument("--b", type=float, default=0.2)  # fitts law param b
parser.add_argument("--c", type=float, default=0.2)  # hicks law param c
parser.add_argument("--d", type=float, default=0.15)  # hicks law param d
parser.add_argument("--E", type=float, default=0.04)  # probability of inputting a wrong letter
parser.add_argument("--target_word", type=str, default="apple")  # word that user has to type

args = parser.parse_args()

if args.random_seed is not None:
    NP_SEED = args.random_seed
    np.random.seed(NP_SEED)
else:
    NP_SEED = None

TARGET_WORD = args.target_word


def np_random_sampler(p):
    return np.random.rand() < p


def fitts_time(a, b, K):
    return a + b * K


def print_row(t, key, result):
    print(f"{t:.2f}\t{key}\t{result}")


if __name__ == "__main__":
    t = 0.0
    print("Time\tTarget\tResult")

    error = False
    replan = True  # set to true initially so the initial planning goes through

    i = 0
    while i < len(TARGET_WORD):
        ch = TARGET_WORD[i]

        # if we need to initialize (during first keystroke or after an error) add latencies
        # for perceiving existing symbols and planning next keystrokes
        if replan:
            t += TAU_P + TAU_C
            # unset the replan flag
            replan = False

        # decide to correct iff we made a mistake (cognition is faster than typing the next letter)
        if error:
            # still, we take TAU_P, becasue although we didnt type, we still took some time perceiving the mistake
            t += TAU_P
            # the spec says:
            # (1) 인지 시스템은 손가락 움직임을 비롯한 모든 프로세스를
            # 멈추기로 결정하고, 이어서 오류를 수정할(백스페이스 키를 누를)움직임을 계획한다
            # so two latencies need to pass, one cognitive latency to decide that an error has been made
            # and another to plan to press the backspace

            # as a result, we need to add to time elapsed 2*TAU_C
            t += 2*TAU_C

            # now we need to actually press the backspace key. this op is assumed error free
            t += fitts_time(args.a, args.b, args.K)
            # log the event because it is observable
            print_row(t, "BS", "success")
            # we didnt make any progress, but we amended the error. unset the error flag
            error = False
            # before the next cycles starts we will need to replan, so set the replan flag
            replan = True
            # move to next cycle to try to replan and then try to type the next char
            continue

        # type the planned letter
        t += fitts_time(args.a, args.b, args.K)

        if np_random_sampler(args.E):
            # the typed event was wrong, but the perceptual system hasnt picked up on that yet
            # still, it is observable so we log the event
            print_row(t, ch, "fail")
            # set the error flag so next cycle we can account for perceiving and correcting
            error = True
        # if we didnt make a mistake
        else:
            # the correct letter being typed is observable, log the event
            print_row(t, ch, "success")
            # we made progress
            i += 1
