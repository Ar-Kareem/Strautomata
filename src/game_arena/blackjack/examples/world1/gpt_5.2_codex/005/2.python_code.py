
from functools import lru_cache

# Fixed deck order
DECK = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
CARD_TO_IDX = {c: i for i, c in enumerate(DECK)}
CARD_VALUE = {str(i): i for i in range(2, 11)}
CARD_VALUE.update({"J": 10, "Q": 10, "K": 10})

def policy(hand: list[str], target: int) -> str:
    # Build mask of remaining cards (1 means available)
    mask = (1 << len(DECK)) - 1
    for c in hand:
        if c in CARD_TO_IDX:
            mask &= ~(1 << CARD_TO_IDX[c])
    
    def hand_value_from_mask(m: int) -> int:
        total = 0
        aces = 0
        for i, card in enumerate(DECK):
            if not (m >> i) & 1:  # card is in hand
                if card == "A":
                    aces += 1
                else:
                    total += CARD_VALUE.get(card, 0)
        total += aces * 11
        while total > target and aces > 0:
            total -= 10
            aces -= 1
        return total

    @lru_cache(maxsize=None)
    def expected_value(m: int) -> float:
        hv = hand_value_from_mask(m)
        if hv > target:
            return 0.0  # bust
        stay_val = float(hv)
        if m == 0:
            return stay_val  # no cards left
        # Expected value if we hit
        cnt = m.bit_count()
        sum_val = 0.0
        mm = m
        while mm:
            lsb = mm & -mm
            idx = (lsb.bit_length() - 1)
            newm = m & ~(1 << idx)
            sum_val += expected_value(newm)
            mm -= lsb
        hit_val = sum_val / cnt
        return max(stay_val, hit_val)

    # Decide action for current state
    hv_now = hand_value_from_mask(mask)
    if hv_now > target or mask == 0:
        return "STAY"
    
    stay_val = float(hv_now)
    # Compute hit expectation
    cnt = mask.bit_count()
    sum_val = 0.0
    mm = mask
    while mm:
        lsb = mm & -mm
        idx = (lsb.bit_length() - 1)
        newm = mask & ~(1 << idx)
        sum_val += expected_value(newm)
        mm -= lsb
    hit_val = sum_val / cnt
    
    if hit_val > stay_val + 1e-9:
        return "HIT"
    else:
        return "STAY"
