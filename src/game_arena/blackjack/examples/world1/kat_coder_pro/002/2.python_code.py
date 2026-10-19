
import numpy as np

def policy(hand: list[str], target: int) -> str:
    # Define card values
    card_values = {
        '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
        'J': 10, 'Q': 10, 'K': 10, 'A': 11  # A will be handled specially
    }
    
    # Define all possible cards
    all_cards = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
    
    # Calculate current hand value (considering A's dual value)
    def get_hand_value(hand_list):
        value = 0
        aces = 0
        
        for card in hand_list:
            if card == 'A':
                aces += 1
                value += 11
            else:
                value += card_values[card]
        
        # Adjust Aces from 11 to 1 if needed to avoid busting
        while value > target and aces > 0:
            value -= 10  # Change an Ace from 11 to 1
            aces -= 1
        
        return value
    
    current_value = get_hand_value(hand)
    
    # If already at or over target, stay
    if current_value >= target:
        return "STAY"
    
    # Determine remaining cards
    remaining_cards = [card for card in all_cards if card not in hand]
    
    # Calculate distance to target
    distance = target - current_value
    
    # If very close to target, be conservative
    if distance <= 2:
        return "STAY"
    
    # Calculate bust probability and expected improvement
    safe_cards = 0
    total_improvement = 0
    
    for card in remaining_cards:
        card_val = card_values[card]
        if card == 'A':
            # Ace can be 1 or 11, we'll consider the safe value (1) for bust calculation
            # but the potential value (11) for improvement
            if current_value + 1 <= target:
                safe_cards += 1
                total_improvement += min(11, distance)
        else:
            if current_value + card_val <= target:
                safe_cards += 1
                total_improvement += min(card_val, distance)
    
    # Probability of not busting
    safe_prob = safe_cards / len(remaining_cards) if remaining_cards else 0
    
    # Decision logic
    # If high chance of safe draw and significant distance to target, hit
    if safe_prob > 0.7 and distance > 4:
        return "HIT"
    elif safe_prob > 0.5 and distance > 6:
        return "HIT"
    elif safe_prob > 0.3 and distance > 8:
        return "HIT"
    else:
        return "STAY"
