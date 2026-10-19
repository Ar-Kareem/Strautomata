
def policy(hand: list[str], target: int) -> str:
    full_deck = {"A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"}
    card_values = {
        "A": 11, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10,
        "J": 10, "Q": 10, "K": 10
    }

    hand_set = set(hand)
    remaining = full_deck - hand_set

    def hand_value(hset: frozenset) -> int:
        total = sum(card_values[c] for c in hset)
        if "A" in hset and total > target:
            total -= 10
        return total

    current_hand_fs = frozenset(hand_set)
    current_v = hand_value(current_hand_fs)
    if current_v > target:
        return "STAY"

    current_rem_fs = frozenset(remaining)
    memo = {}

    def optimal_exp(rem_fs: frozenset) -> float:
        if rem_fs in memo:
            return memo[rem_fs]
        hset = full_deck - rem_fs
        cv = hand_value(frozenset(hset))
        if cv > target:
            memo[rem_fs] = 0.0
            return 0.0
        stay_v = float(cv)
        if not rem_fs:
            memo[rem_fs] = stay_v
            return stay_v
        exp_hit = 0.0
        n = len(rem_fs)
        for c in rem_fs:
            new_rem = rem_fs - frozenset([c])
            new_hset = frozenset(hset | {c})
            new_cv = hand_value(new_hset)
            if new_cv > target:
                sub_v = 0.0
            else:
                sub_v = optimal_exp(new_rem)
            exp_hit += sub_v / n
        best = max(stay_v, exp_hit)
        memo[rem_fs] = best
        return best

    optimal_current = optimal_exp(current_rem_fs)
    if optimal_current > current_v:
        return "HIT"
    else:
        return "STAY"
