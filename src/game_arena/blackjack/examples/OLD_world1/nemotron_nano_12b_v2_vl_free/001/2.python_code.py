
def compute_hand_value(hand, T):
    sum_non_ace = 0
    ace_count = 0
    for card in hand:
        if card == 'A':
            ace_count += 1
        else:
            if card in {'J', 'Q', 'K'}:
                sum_non_ace += 10
            else:
                sum_non_ace += int(card)
    
    sum_all_11 = sum_non_ace + 11 * ace_count
    if sum_all_11 <= T:
        return sum_all_11
    
    sum_all_1 = sum_non_ace + ace_count
    if sum_all_1 > T:
        return sum_all_1  # Busted
    
    available = T - (sum_non_ace + ace_count)
    if available >= 0:
        switches = min(ace_count, available // 10)
        return sum_non_amp + 10 * switches + ace_count
    else:
        return sum_all_1

def compute_probability_of_bust(hand, target):
    current_length = len(hand)
    if current_length >= 13:
        return 1.0  # No cards left to draw, but can't get over target
    
    possible_new_cards = [card for card in "23456789JQKA" if card not in hand]
    total_valid = 0
    
    for new_card in possible_new_cards:
        new_hand = hand + [new_card]
        new_value = compute_hand_value(new_hand, target)
        if new_value <= target:
            total_valid += 1
    
    return 1.0 - (total_valid / len(possible_new_cards))

def policy(hand: list[str], target: int) -> str:
    hand_value = compute_hand_value(hand, target)
    
    if hand_value > target:
        return "STAY"  # Already busted
    if hand_value == target:
        return "STAY"  # Can't improve further
    
    bust_probability_if_hit = compute_probability_of_bust(hand, target)
    
    if bust_probability_if_hit > 0.5:
        return "STAY"
    else:
        return "HIT"
