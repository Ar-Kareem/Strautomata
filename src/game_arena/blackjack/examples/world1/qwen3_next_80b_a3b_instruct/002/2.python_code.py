
def policy(hand: list[str], target: int) -> str:
    def compute_hand_value(hand, T):
        total = 0
        aces = 0
        for card in hand:
            if card == 'A':
                aces += 1
            elif card in ['J', 'Q', 'K']:
                total += 10
            else:
                total += int(card)
        # Calculate candidate score with all aces as 11
        candidate = total + 11 * aces
        if candidate <= T:
            return candidate
        else:
            # Need to convert some aces from 11 to 1 (each conversion reduces score by 10)
            # How many aces need to be converted? We need: candidate - 10 * k <= T
            # -> k >= (candidate - T) / 10
            # Take ceiling of (candidate - T) / 10
            k_needed = (candidate - T + 9) // 10
            k = min(aces, k_needed)
            return candidate - 10 * k

    current_value = compute_hand_value(hand, target)
    # If we are within 5 of the target (i.e., >= target-5), we stay.
    # This is a heuristic that balances risk and reward.
    if current_value >= target - 5:
        return "STAY"
    else:
        return "HIT"
