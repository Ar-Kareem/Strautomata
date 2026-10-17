
import numpy as np

def calculate_hand_value(hand, target):
    total = 0
    aces = 0
    for card in hand:
        if card == 'A':
            total += 11
            aces += 1
        elif card in ['J', 'Q', 'K']:
            total += 10
        else:
            total += int(card)
    # Adjust Aces from 11 to 1 if needed
    while total > target and aces > 0:
        total -= 10
        aces -= 1
    return total

def policy(hand: list[str], target: int) -> str:
    current_value = calculate_hand_value(hand, target)
    if current_value > target:
        return "STAY"  # Shouldn't happen as policy is only called when not busted
    
    if current_value == target:
        return "STAY"
    
    all_cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    remaining_cards = [card for card in all_cards if card not in hand]
    
    if not remaining_cards:
        return "STAY"
    
    bust_penalty = -1e9  # Extremely negative utility for busting
    hit_utility = 0.0
    
    for card in remaining_cards:
        new_hand = hand + [card]
        new_value = calculate_hand_value(new_hand, target)
        
        if new_value > target:
            hit_utility += bust_penalty
        else:
            # Utility is negative of the distance from target (closer is better)
            hit_utility += -(target - new_value)
    
    avg_hit_utility = hit_utility / len(remaining_cards)
    stay_utility = -(target - current_value)
    
    return "HIT" if avg_hit_utility > stay_utility else "STAY"
