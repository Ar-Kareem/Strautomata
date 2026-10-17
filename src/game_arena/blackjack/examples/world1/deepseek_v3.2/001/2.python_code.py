
import functools

# mapping card to index
CARD_TO_INDEX = {
    'A': 0, '2': 1, '3': 2, '4': 3, '5': 4, '6': 5, '7': 6,
    '8': 7, '9': 8, '10': 9, 'J': 10, 'Q': 11, 'K': 12
}
INDEX_TO_CARD = {v: k for k, v in CARD_TO_INDEX.items()}
FACE_VALUES = {
    'A': 11,  # default, will adjust later
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
    'J': 10, 'Q': 10, 'K': 10
}

BUST_PENALTY = 1000  # large penalty for busting

def hand_to_mask(hand):
    """Convert list of card strings to bitmask."""
    mask = 0
    for card in hand:
        mask |= 1 << CARD_TO_INDEX[card]
    return mask

def compute_sum(mask, target):
    """Compute total value of cards in mask for given target."""
    total = 0
    has_ace = False
    for i in range(13):
        if mask & (1 << i):
            card = INDEX_TO_CARD[i]
            if card == 'A':
                has_ace = True
            else:
                total += FACE_VALUES[card]
    if has_ace:
        # Ace counts as 11 if it doesn't cause bust, else 1
        if total + 11 <= target:
            total += 11
        else:
            total += 1
    return total

def dp(target, mask, memo):
    """Return (best_action, best_value) for state (target, mask)."""
    if (target, mask) in memo:
        return memo[(target, mask)]

    current_sum = compute_sum(mask, target)
    if current_sum > target:
        # busted
        memo[(target, mask)] = ("STAY", BUST_PENALTY)
        return memo[(target, mask)]

    # STAY value: absolute difference from target
    stay_diff = abs(current_sum - target)

    # HIT value: average over all possible next cards
    remaining = [i for i in range(13) if not (mask & (1 << i))]
    if not remaining:
        # no cards left, must stay
        memo[(target, mask)] = ("STAY", stay_diff)
        return memo[(target, mask)]

    hit_total = 0.0
    for i in remaining:
        new_mask = mask | (1 << i)
        _, val = dp(target, new_mask, memo)
        hit_total += val
    hit_avg = hit_total / len(remaining)

    if stay_diff <= hit_avg:
        best_action = "STAY"
        best_value = stay_diff
    else:
        best_action = "HIT"
        best_value = hit_avg

    memo[(target, mask)] = (best_action, best_value)
    return memo[(target, mask)]

# Global memoization across calls
_memo = {}

def policy(hand: list[str], target: int) -> str:
    # Convert hand to mask
    mask = hand_to_mask(hand)
    # Compute optimal action using DP
    best_action, _ = dp(target, mask, _memo)
    return best_action
