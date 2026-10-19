
def compute_hand_value(hand: list[str], target: int) -> int:
    """Compute the current hand value according to the game rules."""
    # First, assume all Aces are 11
    sum_with_aces_as_11 = sum(
        11 if card == "A" else
        10 if card in ("J", "Q", "K") else
        int(card) for card in hand
    )

    # If sum_with_aces_as_11 <= target, then all Aces are 11
    if sum_with_aces_as_11 <= target:
        return sum_with_aces_as_11
    else:
        # Otherwise, reduce Aces to 1 until sum <= target or no Aces left
        num_aces = hand.count("A")
        sum_no_aces = sum(
            10 if card in ("J", "Q", "K") else
            int(card) for card in hand if card != "A"
        )
        # The minimal reduction is when we reduce as few Aces as possible
        excess = sum_with_aces_as_11 - target
        num_aces_to_reduce = max(0, min(num_aces, excess // 10 + (1 if excess % 10 != 0 else 0)))
        sum_value = sum_no_aces + 11 * (num_aces - num_aces_to_reduce) + 1 * num_aces_to_reduce
        return sum_value

def policy(hand: list[str], target: int) -> str:
    """Determine whether to HIT or STAY based on the current hand and target."""
    current_value = compute_hand_value(hand, target)
    if current_value >= target:
        return "STAY"  # This case shouldn't happen unless we've already busted

    # If we're within 2 points of target, stay to avoid busting
    if target - current_value <= 2:
        return "STAY"
    else:
        return "HIT"
