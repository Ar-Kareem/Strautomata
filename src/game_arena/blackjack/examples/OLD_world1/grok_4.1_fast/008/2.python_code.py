
def policy(hand: list[str], target: int) -> str:
    all_cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    
    def get_value(h: list[str], t: int) -> int:
        vdict = {"A": 11, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10, "J": 10, "Q": 10, "K": 10}
        total = sum(vdict.get(c, 0) for c in h)
        aces = sum(1 for c in h if c == "A")
        while total > t and aces > 0:
            total -= 10
            aces -= 1
        return total
    
    hand_set = set(hand)
    current_val = get_value(hand, target)
    remaining = [c for c in all_cards if c not in hand_set]
    if not remaining:
        return "STAY"
    
    def best_ev(state: frozenset, memo: dict) -> float:
        if state in memo:
            return memo[state]
        h_list = list(state)
        curr_val = get_value(h_list, target)
        rem = [c for c in all_cards if c not in state]
        if not rem:
            memo[state] = float(curr_val)
            return float(curr_val)
        hit_evs = []
        for nc in rem:
            new_h_list = h_list + [nc]
            new_v = get_value(new_h_list, target)
            if new_v > target:
                hit_evs.append(0.0)
            else:
                new_state = frozenset(new_h_list)
                hit_evs.append(best_ev(new_state, memo))
        ev_hit = sum(hit_evs) / len(hit_evs)
        best = max(float(curr_val), ev_hit)
        memo[state] = best
        return best
    
    memo = {}
    hit_evs = []
    for nc in remaining:
        new_h = hand + [nc]
        new_v = get_value(new_h, target)
        if new_v > target:
            hit_evs.append(0.0)
        else:
            new_state = frozenset(new_h)
            hit_evs.append(best_ev(new_state, memo))
    ev_hit = sum(hit_evs) / len(hit_evs)
    
    if ev_hit > float(current_val):
        return "HIT"
    else:
        return "STAY"
