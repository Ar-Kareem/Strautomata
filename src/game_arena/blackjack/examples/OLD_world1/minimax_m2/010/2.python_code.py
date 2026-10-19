
def policy(hand, target):
    def hand_value(hand, target):
        non_ace_sum = 0
        num_aces = 0
        for card in hand:
            if card == 'A':
                num_aces += 1
            elif card in ['J', 'Q', 'K']:
                non_ace_sum += 10
            else:
                non_ace_sum += int(card)
        total = non_ace_sum
        for _ in range(num_aces):
            if total + 11 <= target:
                total += 11
            else:
                total += 1
        return total
    
    if len(hand) == 0:
        return "HIT"
    
    current_value = hand_value(hand, target)
    
    if current_value >= target - 1:
        return "STAY"
    
    all_ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
    hand_set = set(hand)
    remaining_ranks = [rank for rank in all_ranks if rank not in hand_set]
    
    if len(remaining_ranks) == 0:
        return "STAY"
    
    bust_count = 0
    for card in remaining_ranks:
        new_hand = hand + [card]
        new_value = hand_value(new_hand, target)
        if new_value > target:
            bust_count += 1
    
    p_bust = bust_count / len(remaining_ranks)
    
    if p_bust <= 0.5:
        return "HIT"
    else:
        return "STAY"
