
def policy(hand: list[str], target: int) -> str:
    # Calculate current hand value
    def calculate_value(h):
        value = 0
        aces = 0
        for card in h:
            if card == "A":
                aces += 1
                value += 11
            elif card in ["J", "Q", "K"]:
                value += 10
            else:
                value += int(card)
        # Adjust for aces if value > target
        while value > target and aces > 0:
            value -= 10
            aces -= 1
        return value

    current_value = calculate_value(hand)

    # If already bust or exactly at target, stay
    if current_value > target or current_value == target:
        return "STAY"

    # Track remaining cards in the deck (initially all 13 cards)
    full_deck = {"A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"}
    remaining_cards = full_deck - set(hand)

    # Calculate expected value of remaining cards
    expected_value = 0
    for card in remaining_cards:
        if card == "A":
            # A can be 11 or 1, but we approximate its expected value
            expected_value += 6.5  # (11 + 1) / 2
        elif card in ["J", "Q", "K"]:
            expected_value += 10
        else:
            expected_value += int(card)

    # Calculate probability of busting if we hit
    # This is a simplified approximation (exact calculation is complex)
    # We assume the worst-case scenario where we draw the highest remaining card
    max_possible_draw = max(int(card) if card not in ["J", "Q", "K"] else 10 for card in remaining_cards) if remaining_cards else 0
    potential_bust = current_value + max_possible_draw > target

    # Decision logic
    if current_value >= target - 2:  # Close to target, stay to avoid overshooting
        return "STAY"
    elif potential_bust and (current_value + expected_value / len(remaining_cards)) < target - 2:
        # If hitting risks busting and we're not close to target, stay
        return "STAY"
    else:
        # Otherwise, hit to improve chances of reaching target
        return "HIT"
