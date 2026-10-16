
def policy(hand: list[str], target: int) -> str:
    all_ranks = {"A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"}
    
    def compute_total(cards, T):
        non_ace_total = 0
        aces = 0
        for card in cards:
            if card == "A":
                aces += 1
            else:
                if card in ['J', 'Q', 'K']:
                    non_ace_total += 10
                else:
                    non_ace_total += int(card)
        total = non_ace_total + 11 * aces
        while total > T and aces > 0:
            total -= 10
            aces -= 1
        return total
    
    current_sum = compute_total(hand, target)
    
    if current_sum >= target:
        return "STAY"
    
    hand_set = set(hand)
    remaining_ranks = all_ranks - hand_set
    
    if len(remaining_ranks) == 0:
        return "STAY"
    
    bust_count = 0
    for c in remaining_ranks:
        new_hand = hand + [c]
        new_sum = compute_total(new_hand, target)
        if new_sum > target:
            bust_count += 1
    
    bust_prob = bust_count / len(remaining_ranks)
    
    if bust_prob > 0.5:
        return "STAY"
    else:
        return "HIT"
