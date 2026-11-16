
def policy(hand: list[str], target: int) -> str:
    # Calculate current hand value
    def calculate_value(h):
        value = 0
        aces = 0
        for card in h:
            if card == "A":
                aces += 1
                value += 11
            elif card in {"J", "Q", "K", "10"}:
                value += 10
            else:
                value += int(card)
        # Adjust for aces if needed
        while value > target and aces > 0:
            value -= 10
            aces -= 1
        return value

    current_value = calculate_value(hand)

    # If already busted or at target, stay
    if current_value >= target:
        return "STAY"

    # Count remaining high cards (10, J, Q, K) in the deck
    # Since the deck starts full, subtract the ones already in hand
    high_cards = {"10", "J", "Q", "K"}
    remaining_high = 4 - len([c for c in hand if c in high_cards])

    # Dynamic threshold: stay if within (target - remaining_high * 2)
    threshold = target - (remaining_high * 2)
    if current_value >= threshold:
        return "STAY"
    else:
        return "HIT"
