
import numpy as np

def calculate_value(hand, target):
    values = {'A': 11, '2':2, '3':3, '4':4, '5':5, '6':6, '7':7, '8':8, '9':9, '10':10, 'J':10, 'Q':10, 'K':10}
    sum_val = sum(values[c] for c in hand if c != 'A')
    num_aces = hand.count('A')
    for _ in range(num_aces):
        if sum_val + 11 <= target:
            sum_val += 11
        else:
            sum_val += 1
    return sum_val

def policy(hand, target):
    all_cards = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
    remaining_cards = [c for c in all_cards if c not in hand]
    current_val = calculate_value(hand, target)
    
    # Staying score: negative distance to target
    stay_score = -abs(current_val - target)
    
    # If no cards left, can't hit
    if not remaining_cards:
        return "STAY"
    
    # Compute average hitting score
    hit_scores = []
    for card in remaining_cards:
        new_hand = hand + [card]
        new_val = calculate_value(new_hand, target)
        if new_val > target:
            score = float('-inf')  # Bust
        else:
            score = -abs(new_val - target)
        hit_scores.append(score)
    
    avg_hit_score = sum(hit_scores) / len(hit_scores)
    
    # Choose HIT if expected hitting score is higher
    if avg_hit_score > stay_score:
        return "HIT"
    else:
        return "STAY"
