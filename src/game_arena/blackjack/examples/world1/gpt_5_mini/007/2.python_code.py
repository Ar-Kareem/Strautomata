
from typing import List

RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
VALUE_MAP = {
    "A": 11,  # handle flexibility in hand_value
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10,
    "J": 10, "Q": 10, "K": 10
}

def hand_value(hand: List[str], target: int) -> int:
    """
    Compute the best hand value <= target if possible by treating some Aces as 1 (reduce by 10 each),
    otherwise minimal value (may be > target).
    """
    total = 0
    aces = 0
    for c in hand:
        if c == "A":
            aces += 1
            total += 11
        else:
            total += VALUE_MAP.get(c, 0)
    # Convert Aces from 11 to 1 as needed (reduce by 10 per Ace) to try to get <= target
    while total > target and aces > 0:
        total -= 10
        aces -= 1
    return total

def remaining_deck(hand: List[str]) -> List[str]:
    deck = RANKS.copy()
    # Remove one copy per card in hand (deck has one copy each)
    hand_counts = {}
    for c in hand:
        hand_counts[c] = hand_counts.get(c, 0) + 1
    out = []
    for r in deck:
        # append if not consumed by the hand
        if hand_counts.get(r, 0) > 0:
            hand_counts[r] -= 1
        else:
            out.append(r)
    return out

def policy(hand: List[str], target: int) -> str:
    """
    Decide whether to HIT or STAY given current hand and target.
    Heuristic: compute expected distance to target after one HIT (averaging over remaining cards),
    and compare to current distance, while controlling by a bust-probability threshold.
    """
    # Defensive: if hand already busts
    cur_val = hand_value(hand, target)
    if cur_val > target:
        return "STAY"
    if cur_val == target:
        return "STAY"

    rem = remaining_deck(hand)
    if not rem:
        return "STAY"

    current_distance = abs(target - cur_val)

    # Evaluate each possible next card
    total_distance = 0.0
    busts = 0
    for c in rem:
        new_hand = hand + [c]
        new_val = hand_value(new_hand, target)
        if new_val > target:
            # Penalize bust with a large distance (use target as a reasonable upper bound)
            total_distance += float(target)
            busts += 1
        else:
            total_distance += abs(target - new_val)
    n = len(rem)
    expected_distance = total_distance / n
    bust_prob = busts / n

    # Adaptive threshold: be more willing to risk if current distance is large
    threshold = 0.5
    if current_distance >= 6:
        threshold += 0.15
    if current_distance >= 10:
        threshold += 0.15
    # clamp
    if threshold > 0.9:
        threshold = 0.9

    # Decision rule: hit if expected distance improves and bust prob acceptable
    if expected_distance < current_distance and bust_prob <= threshold:
        return "HIT"
    else:
        return "STAY"

# If this file is used as a module, policy(...) is the required entry point.
if __name__ == "__main__":
    # simple quick self-test examples
    examples = [
        (["10"], 21),
        (["A", "9"], 21),
        (["7", "8"], 18),
        (["K", "Q"], 20),
        (["A", "K"], 21),
    ]
    for h, t in examples:
        print(h, t, "->", policy(h, t))
