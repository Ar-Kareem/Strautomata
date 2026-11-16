
from typing import List

ALL_RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
VALUE_MAP = {
    "A": 11,  # base value; we'll handle flexibility separately
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "10": 10,
    "J": 10,
    "Q": 10,
    "K": 10,
}

def best_total_for_hand(hand: List[str], target: int) -> int:
    """
    Return the best total for 'hand' given the target:
    - Choose Ace(s) as 11 or 1 so that the sum is the largest possible value <= target.
    - If no choice gets <= target, return the minimal total (all Aces = 1).
    """
    non_ace_sum = 0
    aces = 0
    for r in hand:
        if r == "A":
            aces += 1
        else:
            non_ace_sum += VALUE_MAP[r]
    # If no aces, just return sum (may be > target).
    if aces == 0:
        return non_ace_sum
    # Try to maximize total <= target by choosing number of aces counted as 11.
    # Total = non_ace_sum + aces*1 + 10*k where k is number of aces counted as 11.
    base = non_ace_sum + aces  # all aces counted as 1
    best = None
    # k from aces down to 0 to find largest total <= target quickly
    for k in range(aces, -1, -1):
        total = base + 10 * k
        if total <= target:
            best = total
            break
    if best is not None:
        return best
    # no choice keeps us <= target: return minimal total (all aces=1)
    return base

def policy(hand: List[str], target: int) -> str:
    """
    Decide whether to "HIT" or "STAY" given current hand and target.
    Strategy:
    - Compute current best total (max <= target if possible).
    - If current total is already within 3 of target, STAY (conservative).
    - Evaluate all possible next ranks remaining in our deck (one of each rank,
      excluding ranks in hand). For each rank, compute resulting best total.
    - Compute expected distance to target after drawing (treat busts as penalty = target).
    - If expected distance < current distance, return "HIT", else "STAY".
    """
    # Defensive: if hand is empty or full, handle trivially
    if hand is None:
        hand = []
    # If already have all cards or no remaining cards, stay
    if len(hand) >= len(ALL_RANKS):
        return "STAY"

    # Current best total
    current_total = best_total_for_hand(hand, target)

    # If already busted (no ace flexibility can avoid > target), stay (or it's too late)
    if current_total > target:
        return "STAY"

    # Conservative threshold: if close to target, don't risk
    if current_total >= target - 3:
        return "STAY"

    # Build remaining ranks in our deck (one of each rank excluding those we've used)
    # Note: if hand has duplicates (shouldn't in valid games), remove that many; here ranks are unique
    remaining = []
    hand_counts = {}
    for r in hand:
        hand_counts[r] = hand_counts.get(r, 0) + 1
    for r in ALL_RANKS:
        # include rank if not fully used; in this simplified model there's only one copy each
        if hand_counts.get(r, 0) == 0:
            remaining.append(r)

    if not remaining:
        return "STAY"

    # Compute expected distance after drawing one card
    current_distance = target - current_total  # >= 0
    penalty_bust = target  # penalty distance for bust outcome

    total_distance = 0.0
    for r in remaining:
        new_hand = hand + [r]
        new_total = best_total_for_hand(new_hand, target)
        if new_total <= target:
            new_distance = target - new_total
        else:
            new_distance = penalty_bust
        total_distance += new_distance
    expected_distance = total_distance / len(remaining)

    # If expected distance improves (is smaller), it's worth hitting
    if expected_distance < current_distance:
        return "HIT"
    else:
        return "STAY"

# If this file is imported, policy() is the intended entry point.
if __name__ == "__main__":
    # quick self-test examples (not required by the arena)
    tests = [
        (["10"], 21),
        (["A", "9"], 21),
        (["A", "9"], 20),
        (["5", "7"], 15),
        (["K", "Q"], 19),
    ]
    for h, t in tests:
        print(h, t, "->", policy(h, t))
