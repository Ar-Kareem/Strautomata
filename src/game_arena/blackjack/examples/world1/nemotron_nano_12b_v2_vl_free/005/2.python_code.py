
def policy(hand, target):
    # Helper function to calculate the hand's value considering Ace adjustments
    def calculate_value(hand, target):
        sum_val = 0
        aces = 0
        for card in hand:
            if card == 'A':
                sum_val += 1
                aces += 1
            elif card in {'J', 'Q', 'K'}:
                sum_val += 10
            else:
                # Convert card value to integer
                sum_val += int(card)
        
        # Adjust for Aces if possible
        while aces > 0 and (sum_val + 10) <= target:
            sum_val += 10
            aces -= 1
        
        return sum_val
    
    current_sum = calculate_value(hand, target)
    
    # If current sum exceeds target, must stay
    if current_sum > target:
        return "STAY"
    
    # Determine available cards in the deck (not in hand)
    all_cards = {'A', '2', '3', '4', '5', '6', '7', '8', '9', 'J', 'Q', 'K', '10'}
    available_cards = list(all_cards - set(hand))
    
    # No cards left to draw
    if not available_cards:
        return "STAY"
    
    # Check if any draw improves our situation without busting
    improved_possible = False
    for card in available_cards:
        new_hand = hand + [card]
        new_sum = calculate_value(new_hand, target)
        if new_sum <= target and new_sum > current_sum:
            improved_possible = True
            break
    
    return "HIT" if improved_possible else "STAY"
