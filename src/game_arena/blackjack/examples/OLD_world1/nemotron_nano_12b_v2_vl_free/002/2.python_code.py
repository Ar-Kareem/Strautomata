
def policy(hand: list[str], target: int) -> str:
    def card_value(card):
        if card == 'A':
            return 11
        elif card in {'J', 'Q', 'K'}:
            return 10
        else:
            return int(card)

    def calculate_hand_value(hand, target):
        total = 0
        aces = 0
        for card in hand:
            if card == 'A':
                total += 11
                aces += 1
            elif card in {'J', 'Q', 'K'}:
                total += 10
            else:
                total += int(card)
        
        # If sum is <= target, return it
        if total <= target:
            return total
        
        # Try converting aces to 1 to reduce sum
        while aces > 0 and total > target:
            total -= 10
            ace_count -= 1
        if total <= target:
            return total
        return float('inf')  # Bust

    # Compute current hand value
    current_value = calculate_hand_value(hand, target)

    if current_value == float('inf'):
        return 'STAY'  # Already busted

    # Identify remaining cards in deck
    all_cards = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
    remaining_cards = [c for c in all_cards if c not in hand]

    if not remaining_cards:
        return 'STAY'  # No cards left to draw

    # Count how many new cards will result in a bust
    bust_count = 0
    for c in remaining_cards:
        new_hand = hand + [c]
        new_value = calculate_hand_value(new_hand, target)
        if new_value > target:
            bust_count += 1

    bust_probability = bust_count / len(remaining_cards)

    # If bust probability is high (>50%), stay
    if bust_probability > 0.5:
        return 'STAY'
    else:
        return 'HIT'
