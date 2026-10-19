
import functools

def policy(hand: list[str], target: int) -> str:
    full_cards = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
    N = 13
    card_to_idx = {c: i for i, c in enumerate(full_cards)}
    card_basevals = [11, 2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10]

    def hand_value(mask: int, t: int) -> int:
        total = 0
        has_ace = False
        for i in range(N):
            if mask & (1 << i):
                bv = card_basevals[i]
                if bv == 11:  # A
                    has_ace = True
                else:
                    total += bv
        if not has_ace:
            return total
        total11 = total + 11
        if total11 <= t:
            return total11
        return total + 1

    BUST_U = -100000.0
    def close_u(v: int, t: int) -> float:
        return -abs(v - t)

    @functools.lru_cache(None)
    def get_val(mask: int) -> float:
        v = hand_value(mask, target)
        stay_u = close_u(v, target)
        rem = [i for i in range(N) if not (mask & (1 << i))]
        nrem = len(rem)
        if nrem == 0:
            return stay_u
        hit_u = 0.0
        for i in rem:
            newmask = mask | (1 << i)
            newv = hand_value(newmask, target)
            if newv > target:
                hit_u += BUST_U
            else:
                hit_u += get_val(newmask)
        hit_u /= nrem
        return max(stay_u, hit_u)

    # Compute current mask
    mask = 0
    for c in hand:
        if c in card_to_idx:
            mask |= (1 << card_to_idx[c])

    v = hand_value(mask, target)
    if v > target:
        return "STAY"

    # Force compute to fill cache
    _ = get_val(mask)

    # Compute stay_u and hit_u
    stay_u = close_u(v, target)
    rem = [i for i in range(N) if not (mask & (1 << i))]
    nrem = len(rem)
    if nrem == 0:
        return "STAY"
    hit_u = 0.0
    for i in rem:
        newmask = mask | (1 << i)
        newv = hand_value(newmask, target)
        if newv > target:
            hit_u += BUST_U
        else:
            hit_u += get_val(newmask)
    hit_u /= nrem

    if hit_u > stay_u:
        return "HIT"
    else:
        return "STAY"
