
import numpy as np

def policy(hand: list[str], target: int) -> str:
    # Card value mapping
    value_map = {str(i): i for i in range(2, 11)}
    value_map.update({'J': 10, 'Q': 10, 'K': 10, 'A': 11})
    
    # Calculate current hand value with soft A
    def hand_value(hand):
        total = 0
        a_count = 0
        for card in hand:
            val = value_map[card]
            if card == 'A':
                a_count += 1
                total += 11
            else:
                total += val
        
        # Adjust A values if needed
        while total > target and a_count > 0:
            total -= 10  # Change A from 11 to 1
            a_count -= 1
        return total
    
    current_value = hand_value(hand)
    
    # If already at or above target, stay
    if current_value >= target:
        return "STAY"
    
    # If current value is high, be conservative
    if current_value >= target - 2:
        return "STAY"
    
    # If current value is very low, always hit
    if current_value <= 11:
        return "HIT"
    
    # Otherwise, use a threshold-based strategy
    # Higher threshold when closer to target
    threshold = target - 4
    if current_value >= threshold:
        return "STAY"
    else:
        return "HIT"
