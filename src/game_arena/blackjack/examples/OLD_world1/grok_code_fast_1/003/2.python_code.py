
import math
import random
import numpy as np  # Not used in this implementation, but allowed

def hand_value(hand, target):
    sum_temp = 0
    num_ace = 0
    for card in hand:
        if card == "A":
            sum_temp += 11
            num_ace += 1
        elif card in ["J", "Q", "K"]:
            sum_temp += 10
        else:
            sum_temp += int(card)
    sum_with_ace_1 = sum_temp - 10 * num_ace
    if sum_with_ace_1 <= target:
        return sum_with_ace_1
    elif sum_temp <= target:
        return sum_temp
    else:
        return sum_temp  # Will be > target, treated as bust

def policy(hand: list[str], target: int) -> str:
    my_deck = ["A"] + [str(i) for i in range(2, 11)] + ["J", "Q", "K"]
    remaining = [c for c in my_deck if c not in hand]
    current_value = hand_value(hand, target)
    
    if not remaining:
        return "STAY"  # No cards left, must stay
    
    total_score = 0.0
    count = 0
    for card in remaining:
        new_hand = hand + [card]
        new_v = hand_value(new_hand, target)
        if new_v > target:
            score = float('-inf')
        else:
            score = new_v
        total_score += score
        count += 1
    
    if count > 0:
        expected_score_hit = total_score / count
    else:
        expected_score_hit = float('-inf')
    
    if expected_score_hit > current_value:
        return "HIT"
    else:
        return "STAY"
