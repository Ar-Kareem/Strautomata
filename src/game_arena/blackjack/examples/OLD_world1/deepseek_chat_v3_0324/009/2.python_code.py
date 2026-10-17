
import random

def calculate_hand_value(hand: list[str], target: int) -> int:
    value = 0
    aces = 0
    
    for card in hand:
        if card == 'A':
            value += 11
            aces += 1
        elif card in ['J', 'Q', 'K']:
            value += 10
        else:
            value += int(card)
    
    # Adjust for aces if needed
    while value > target and aces > 0:
        value -= 10
        aces -= 1
    
    return value

def policy(hand: list[str], target: int) -> str:
    current_value = calculate_hand_value(hand, target)
    
    # If already at or above target, we must stay
    if current_value >= target:
        return "STAY"
    
    # Calculate remaining cards in deck (our unseen cards)
    full_deck = {'A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K'}
    seen_cards = set(hand)
    remaining_cards = list(full_deck - seen_cards)
    
    # Calculate probabilities of different outcomes if we hit
    prob_bust = 0
    possible_values = []
    
    for card in remaining_cards:
        if card == 'A':
            test_value = current_value + 11
            if test_value > target:
                test_value = current_value + 1
        elif card in ['J', 'Q', 'K']:
            test_value = current_value + 10
        else:
            test_value = current_value + int(card)
        
        possible_values.append(test_value)
    
    prob_bust = sum(1 for val in possible_values if val > target) / len(possible_values)
    expected_value = sum(possible_values) / len(possible_values)
    median_value = sorted(possible_values)[len(possible_values)//2]
    
    # Decide whether to hit or stay based on multiple factors
    remaining_distance = target - current_value
    
    # Conservative strategy for higher targets
    if target >= 25:
        if current_value >= target - 5:
            return "STAY"
        else:
            if prob_bust < 0.5:
                return "HIT"
            else:
                return "STAY"
    
    # Aggressive strategy for lower targets
    else:
        if remaining_distance >= 10:
            return "HIT"
        elif remaining_distance >= 5 and prob_bust < 0.4:
            return "HIT"
        else:
            if prob_bust < 0.5 and current_value <= target - 2:
                return "HIT"
            else:
                return "STAY"
