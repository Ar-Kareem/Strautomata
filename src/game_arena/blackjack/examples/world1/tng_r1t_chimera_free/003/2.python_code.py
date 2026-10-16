
def policy(hand: list[str], target: int) -> str:
    def calculate_hand_value(hand, target):
        total = 0
        aces = 0
        
        for card in hand:
            if card == 'A':
                aces += 1
            elif card in {'J', 'Q', 'K'}:
                total += 10
            else:
                total += int(card)
                
        total += 11 * aces
        
        while total > target and aces > 0:
            total -= 10
            aces -= 1
        
        return total
    
    current_value = calculate_hand_value(hand, target)
    
    if current_value > target:
        return "STAY"
    
    if current_value + 2 <= target:
        return "HIT"
    else:
        return "STAY"
