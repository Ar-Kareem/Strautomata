
def compute_hand_value(hand, target):
    total = 0
    ace_count = 0
    for card in hand:
        if card == 'A':
            ace_count += 1
            total += 11
        elif card in ['J', 'Q', 'K']:
            total += 10
        else:
            total += int(card)
    # Adjust Aces: reduce from 11 to 1 (subtract 10) until total <= target or no Aces left
    while total > target and ace_count > 0:
        total -= 10
        ace_count -= 1
    return total

def policy(hand, target):
    current_score = compute_hand_value(hand, target)
    if current_score > target or current_score == target:
        return "STAY"
    
    full_deck = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    remaining_cards = [card for card in full_deck if card not in hand]
    
    if not remaining_cards:
        return "STAY"
    
    bust_count = 0
    for card in remaining_cards:
        new_hand = hand + [card]
        new_score = compute_hand_value(new_hand, target)
        if new_score > target:
            bust_count += 1
    
    bust_prob = bust_count / len(remaining_cards)
    return "STAY" if bust_prob >= 0.5 else "HIT"
