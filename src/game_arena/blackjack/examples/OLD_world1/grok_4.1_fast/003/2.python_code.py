
def policy(hand: list[str], target: int) -> str:
    def hand_value(h: list[str], t: int) -> int:
        non_ace_sum = 0
        num_aces = 0
        for card in h:
            if card == 'A':
                num_aces += 1
            else:
                if card in {'J', 'Q', 'K'}:
                    non_ace_sum += 10
                else:
                    non_ace_sum += int(card)
        total = non_ace_sum + 11 * num_aces
        aces_adjust = num_aces
        while total > t and aces_adjust > 0:
            total -= 10
            aces_adjust -= 1
        return total

    def get_value(hand_set: frozenset, t: int, memo: dict) -> float:
        if hand_set in memo:
            return memo[hand_set]
        current_h = list(hand_set)
        curr_score = hand_value(current_h, t)
        if curr_score > t:
            val = -1.0
        else:
            stay_val = float(curr_score)
            all_cards = frozenset({"A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"})
            rem = all_cards - hand_set
            if not rem:
                val = stay_val
            else:
                hit_val = 0.0
                n = len(rem)
                for r in rem:
                    new_set = hand_set | frozenset([r])
                    new_h = current_h + [r]
                    new_score = hand_value(new_h, t)
                    if new_score > t:
                        this_val = -1.0
                    else:
                        this_val = get_value(new_set, t, memo)
                    hit_val += this_val / n
                val = max(stay_val, hit_val)
        memo[hand_set] = val
        return val

    h_set = frozenset(hand)
    curr_score = hand_value(hand, target)
    all_cards = frozenset({"A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"})
    rem = all_cards - h_set
    if curr_score > target or not rem:
        return "STAY"
    memo = {}
    hit_val = 0.0
    n = len(rem)
    for r in rem:
        new_list = hand + [r]
        new_set = h_set | frozenset([r])
        new_score = hand_value(new_list, target)
        if new_score > target:
            this_val = -1.0
        else:
            this_val = get_value(new_set, target, memo)
        hit_val += this_val / n
    stay_val = float(curr_score)
    if hit_val > stay_val:
        return "HIT"
    else:
        return "STAY"
