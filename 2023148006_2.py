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


def np_random_sampler(p):
    return np.random.rand() < p


def fitts_time(a, b, K):
    return a + b * K


def hicks_time(a, b, N):
    return a + b * np.log2(N)


def p_ac_success(N, M):
    return 1 - np.exp(-((M * 8.6**N)/(80000)))


def print_row(t, key, result):
    print(f"{t:.2f}\t{key}\t{result}")


def simulate(args, suppress_output=False):
    if args.random_seed is not None:
        NP_SEED = args.random_seed
        np.random.seed(NP_SEED)
    else:
        NP_SEED = None

    TARGET_WORD = args.target_word

    t = 0.0
    if not suppress_output:
        print("Time\tTarget\tResult")

    error = False
    replan = True  # set to true initially so the initial planning goes through
    ac_valid = False
    ac_successful = False

    i = 0
    while i < len(args.target_word):
        ch = args.target_word[i]

        # if we need to initialize (during first keystroke or after an error) add latencies
        # for perceiving existing symbols and planning next keystrokes
        if replan:
            t += TAU_P + TAU_C
            # unset the replan flag
            replan = False
            # actually i was thinking of adding a compensation variable for when the user needs
            # to think about what they are going to type (the system delay L for autocompletes)
            # can elapse while the user is processing
            #
            # but this replan branch is reached iff the ac_valid is set to False, so the situation
            # where the delay is elapsing while the user is processing wont ever happen so i chose
            # to omit the compensation code to get a cleaner source

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
            if not suppress_output:
                print_row(t, "BS", "success")
            # we didnt make any progress, but we amended the error. unset the error flag
            error = False
            # before the next cycles starts we will need to replan, so set the replan flag
            replan = True
            # per spec:
            # Q5) BS를 누른 경우의 추천 단어 시스템 작동에 대한 질문
            # BS를 누른 경우에는 추천단어가 존재하지 않고 계획된 다음 운동계획을 시작합니다.

            # -> i.e. BS unsets autocomplete validity
            ac_valid = False

            # move to next cycle to try to replan and then try to type the next char
            continue

        # type the planned letter or autocomplete, depends on which one appears first
        # although the spec didnt explicitly mention that it is assumed that autocomplete evaluation
        # is slower than error checking (like the typing procedure)
        # we will assume that this is the case, because the spec doesnt actually say anything about it
        if ac_successful and ac_valid:
            # if autocomplete was successful and it is valid we have to consider which will happen faster:
            # 1) typing the next letter
            # 2) waiting for system delay + hicks time to discern the correct autocomplete option + cognitive system
            #    deciding whether to keep typing or pressing autocomplete
            dt_type = fitts_time(args.a, args.b, args.K)
            dt_auto = args.L + hicks_time(args.c, args.d, args.N) + TAU_C

            # this path effectively fires immediately after the previous cycle
            # ended with the user typing a letter (not BS because if that wouldve been the case, we wouldnt be here)
            #
            # so since we are operating with deltas, we can just compare them to correctly account for system delay

            # if dt_type is smaller, then the user typed faster than they could see an autocomplete suggestion
            if dt_type < dt_auto:
                t += dt_type
            # if dt_auto is smaller or equal, the user is able to detect the intended word. they press it instantaneously
            else:
                t += dt_auto
                # autocomplete action is visible, log it
                if not suppress_output:
                    print_row(t, "AC", "success")
                # autocomplete means we are good to leave & finish simulation
                return t
        # if ac is either not successful or not valid, we will end up typing anyway so just type
        else:
            t += fitts_time(args.a, args.b, args.K)

        if np_random_sampler(args.E):
            # the typed event was wrong, but the perceptual system hasnt picked up on that yet
            # still, it is observable so we log the event
            if not suppress_output:
                print_row(t, ch, "fail")
            # set the error flag so next cycle we can account for perceiving and correcting
            error = True

            # originally, i wanted to do this:
            # <<<<<<<<<<<<<< ORIGINAL IMPLEMENTATION
            # # update the autocomplete suggestions for next iteration
            # # the spec mentions:
            # # Q7) 추천단어 처리 프로세스가 길어서 처리 중에 다음 손가락 운동 계획이 실행된 경우
            # # A7) 이 경우 기존의 추천단어 처리 프로세스는 중단되고, 새로운 추천단어 처리 프로세스가 병렬적으로 실행된다고 가정합니다.
            # #
            # # -> if we typed faster than we got the autocomplete suggestion, the autocomplete resets and starts anew
            # # we can be in this codepath only if the AC was unsuccessful or slower than the typing speed so this
            # # effectively implements Q7
            # # add 1 to i because we typed one more letter
            # ac_successful = np_random_sampler(p_ac_success(args.N, i + 1))
            # # mark autocomplete valid
            # ac_valid = True
            # >>>>>>>>>>>>>> ORIGINAL IMPLEMENTATION

            # but we will go with invalidating the autocomplete suggestions. that makes more sense because
            # if we input a wrong letter, then whatever the autocomplete will suggest will be wrong or outright impossible
            ac_successful = False

        # if we didnt make a mistake
        else:
            # the correct letter being typed is observable, log the event
            if not suppress_output:
                print_row(t, ch, "success")
            # we made progress
            i += 1
            # update the autocomplete suggestions for next iteration

            # the spec mentions:
            # Q7) 추천단어 처리 프로세스가 길어서 처리 중에 다음 손가락 운동 계획이 실행된 경우
            # A7) 이 경우 기존의 추천단어 처리 프로세스는 중단되고, 새로운 추천단어 처리 프로세스가 병렬적으로 실행된다고 가정합니다.
            #
            # -> if we typed faster than we got the autocomplete suggestion, the autocomplete resets and starts anew
            # we can be in this codepath only if the AC was unsuccessful or slower than the typing speed so this
            # effectively implements Q7
            ac_successful = np_random_sampler(p_ac_success(args.N, i))
            # mark autocomplete valid
            ac_valid = True

    return t


if __name__ == "__main__":
    args = parser.parse_args()

    if args.random_seed is not None:
        NP_SEED = args.random_seed
        np.random.seed(NP_SEED)
    else:
        NP_SEED = None

    TARGET_WORD = args.target_word

    t_final = simulate(args, suppress_output=False)
