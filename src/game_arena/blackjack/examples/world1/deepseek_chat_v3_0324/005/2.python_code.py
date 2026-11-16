
import random

def calculate_hand_value(hand, target):
    value = 0
    aces = 0
    
    # First pass: count non-ace cards
    for card in hand:
        if card == 'A':
            aces += 1
        elif card in ['J', 'Q', 'K']:
            value += 10
        else:  # 2-10
            value += int(card)
    
    # Second pass: handle aces
    for _ in range(aces):
        # Ace counts as 11 if it won't make us exceed target
        if value + 11 <= target:
            value += 11
        else:
            value += 1
    
    return value

def policy(hand: list[str], target: int) -> str:
    current_value = calculate_hand_value(hand, target)
    
    # If we've reached or exceeded target, stay
    if current_value >= target:
        return "STAY"
    
    # Calculate remaining cards in our deck
    all_cards = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
    remaining_cards = [card for card in all_cards if card not in hand]
    
    # Calculate probabilities of different outcomes if we hit
    bust_probability = 0.0
    improve_probability = 0.0
    
    for card in remaining_cards:
        # Calculate new value if we draw this card
        new_hand = hand + [card]
        new_value = calculate_hand_value(new_hand, target)
        
        if new_value > target:
            bust_probability += 1
        else:
            improve_probability += 1
    
    total_possible = len(remaining_cards)
    if total_possible > 0:
        bust_probability /= total_possible
        improve_probability /= total_possible
    
    # Decision logic
    if current_value >= target - 5 and bust_probability > 0.5:
        return "STAY"
    elif current_value < target - 10:
        return "HIT"
    else:
        # More conservative approach when close to target
        if bust_probability < 0.4:
            return "HIT"
        else:
            return "STAY"
