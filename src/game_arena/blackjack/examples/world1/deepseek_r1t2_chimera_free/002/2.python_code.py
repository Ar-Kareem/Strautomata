
def policy(hand: list[str], target: int) -> str:
    full_deck = {"A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"}
    
    def calculate_hand_value(hand, target):
        total = 0
        aces = 0
        for card in hand:
            if card == 'A':
                aces += 1
            elif card in ['J', 'Q', 'K']:
                total += 10
            else:
                total += int(card)
        for _ in range(aces):
            if total + 11 <= target:
                total += 11
            else:
                total += 1
        return total
    
    current_score = calculate_hand_value(hand, target)
    remaining_cards = list(full_deck - set(hand))
    
    if not remaining_cards or current_score == target:
        return "STAY"
    
    bust_count = 0
    all_bust = True
    no_bust = True
    
    for card in remaining_cards:
        if card == 'A':
            if current_score + 11 <= target:
                add_val = 11
            else:
                add_val = 1
        elif card in ['J', 'Q', 'K']:
            add_val = 10
        else:
            add_val = int(card)
        new_score = current_score + add_val
        if new_score > target:
            bust_count += 1
            no_bust = False
        else:
            all_bust = False
            
    if all_bust:
        return "STAY"
    if no_bust:
        return "HIT"
    
    bust_prob = bust_count / len(remaining_cards)
    return "HIT" if bust_prob < 0.5 else "STAY"
