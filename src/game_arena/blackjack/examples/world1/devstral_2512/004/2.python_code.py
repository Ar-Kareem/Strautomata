
import random
from collections import defaultdict

def calculate_hand_value(hand, target):
    value = 0
    aces = 0
    for card in hand:
        if card in ['J', 'Q', 'K']:
            value += 10
        elif card == 'A':
            value += 11
            aces += 1
        else:
            value += int(card)

    # Adjust for aces if we're over target
    while value > target and aces > 0:
        value -= 10
        aces -= 1

    return value

def policy(hand, target):
    # Calculate current hand value
    current_value = calculate_hand_value(hand, target)

    # If we're already at or above target, stay
    if current_value >= target:
        return "STAY"

    # If we're very close to target (within 3), be more conservative
    if current_value >= target - 3:
        # Calculate probability of busting
        remaining_cards = [c for c in ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K'] if c not in hand]
        bust_prob = sum(1 for card in remaining_cards
                       if (card in ['J', 'Q', 'K'] and current_value + 10 > target) or
                          (card != 'A' and current_value + int(card) > target) or
                          (card == 'A' and current_value + 11 > target and current_value + 1 > target)) / len(remaining_cards)

        # If high chance of busting, stay
        if bust_prob > 0.5:
            return "STAY"

    # If we're far from target, be more aggressive
    # Calculate expected value of hitting
    remaining_cards = [c for c in ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K'] if c not in hand]
    if not remaining_cards:
        return "STAY"

    # Calculate average improvement from hitting
    avg_improvement = sum(
        min(11, target - current_value) if card == 'A' else
        min(10, target - current_value) if card in ['J', 'Q', 'K'] else
        min(int(card), target - current_value)
        for card in remaining_cards
    ) / len(remaining_cards)

    # If average improvement is significant, hit
    if avg_improvement > 2:
        return "HIT"

    # Default to more conservative play
    if current_value >= target - 5:
        return "STAY"
    else:
        return "HIT"
