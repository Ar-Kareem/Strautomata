
def calculate_hand_value(hand, target):
    total = 0
    aces = 0
    for card in hand:
        if card == 'A':
            total += 11
            aces += 1
        elif len(card) == 1:
            total += int(card)
        else:
            total += 10
    # Adjust Aces if exceeding target
    while aces > 0 and total > target:
        total -= 10
        aces -= 1
    return total

def policy(hand, target):
    current_sum = calculate_hand_value(hand, target)
    if current_sum > target:
        return 'STAY'
    
    all_cards = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
    remaining = [c for c in all_cards if c not in hand]
    
    # If no remaining cards, stay
    if not remaining:
        return 'STAY'
    
    # Calculate average value of remaining cards in our deck
    avg_card_value = 0.0
    count = len(remaining)
    for c in remaining:
        # Calculate value of current hand if this card is added
        trial_hand = hand + [c]
        trial_sum = calculate_hand_value(trial_hand, target)
        if trial_sum <= target:
            avg_card_value += min(trial_sum, target)
        else:
            avg_card_value += 0  # Bust, contributes 0 to win chances
    
    avg_card_value /= count
    
    # Determine if hitting improves expected value
    if avg_card_value > current_sum:
        return 'HIT'
    else:
        return 'STAY'
