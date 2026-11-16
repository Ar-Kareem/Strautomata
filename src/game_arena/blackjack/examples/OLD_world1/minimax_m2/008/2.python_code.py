
def policy(hand, target):
    def hand_value(cards, target_score):
        total = 0
        for card in cards:
            if card == 'A':
                if total + 11 <= target_score:
                    total += 11
                else:
                    total += 1
            elif card in ['J', 'Q', 'K']:
                total += 10
            else:
                total += int(card)
        return total

    current_value = hand_value(hand, target)
    
    if current_value >= target - 2:
        return "STAY"
    
    deck_ranks = {'A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K'}
    remaining_cards = deck_ranks - set(hand)
    
    bust_count = 0
    for card in remaining_cards:
        if card == 'A':
            if current_value + 11 <= target:
                new_total = current_value + 11
            else:
                new_total = current_value + 1
        elif card in ['J', 'Q', 'K']:
            new_total = current_value + 10
        else:
            new_total = current_value + int(card)
        if new_total > target:
            bust_count += 1
    
    if len(remaining_cards) > 0:
        bust_probability = bust_count / len(remaining_cards)
    else:
        bust_probability = 0
        
    if bust_probability >= 0.5:
        return "STAY"
    else:
        return "HIT"
