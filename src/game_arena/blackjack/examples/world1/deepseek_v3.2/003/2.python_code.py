
def hand_value(hand, target):
    """Calculate total value of hand according to the rules."""
    sum_non_ace = 0
    num_aces = 0
    for card in hand:
        if card == 'A':
            num_aces += 1
        elif card in ('J', 'Q', 'K'):
            sum_non_ace += 10
        else:  # '2'..'10'
            sum_non_ace += int(card)
    
    # Start with all aces as 11
    total = sum_non_ace + 11 * num_aces
    
    # Convert aces from 11 to 1 if we are above target
    while total > target and num_aces > 0:
        total -= 10
        num_aces -= 1
    
    return total


def policy(hand: list[str], target: int) -> str:
    # All possible cards in the deck
    all_cards = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
    
    # Cards still in our deck (not yet drawn)
    remaining = [c for c in all_cards if c not in hand]
    
    # If no cards left, we must stay
    if not remaining:
        return "STAY"
    
    current_val = hand_value(hand, target)
    
    # If we are already at target, staying is optimal
    if current_val == target:
        return "STAY"
    
    # Compute utility of staying: negative distance to target
    stay_utility = -abs(current_val - target)
    
    # Compute expected utility of drawing one more card and then staying
    hit_utilities = []
    bust_penalty = -1000  # large negative for busting
    
    for card in remaining:
        new_hand = hand + [card]
        new_val = hand_value(new_hand, target)
        if new_val > target:
            # Bust
            hit_utilities.append(bust_penalty)
        else:
            # Not bust, utility is negative distance
            hit_utilities.append(-abs(new_val - target))
    
    expected_hit_utility = sum(hit_utilities) / len(hit_utilities)
    
    # Choose action with higher expected utility
    if expected_hit_utility > stay_utility:
        return "HIT"
    else:
        return "STAY"
