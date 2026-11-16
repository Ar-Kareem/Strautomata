
import random

def calculate_hand_value(hand: list[str], target: int) -> int:
    """Calculate the current hand value considering Aces properly."""
    value = 0
    aces = 0
    
    for card in hand:
        if card == 'A':
            aces += 1
            value += 11
        elif card in ['J', 'Q', 'K']:
            value += 10
        else:  # 2-10
            value += int(card)
    
    # Adjust for aces if needed
    while value > target and aces > 0:
        value -= 10  # Convert an Ace from 11 to 1
        aces -= 1
    
    return value

def policy(hand: list[str], target: int) -> str:
    current_value = calculate_hand_value(hand, target)
    
    # If we're at or over target, stay to avoid busting
    if current_value >= target:
        return "STAY"
    
    # Calculate remaining cards in our deck
    all_cards = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
    remaining_cards = [card for card in all_cards if card not in hand]
    
    # Calculate possible outcomes if we hit
    possible_values = []
    for card in remaining_cards:
        new_hand = hand.copy()
        new_hand.append(card)
        possible_values.append(calculate_hand_value(new_hand, target))
    
    # Calculate probabilities
    safe_hits = sum(1 for val in possible_values if val <= target)
    busts = len(possible_values) - safe_hits
    safe_prob = safe_hits / len(remaining_cards) if remaining_cards else 0
    
    # Decision making
    if not remaining_cards:  # No cards left, must stay
        return "STAY"
    
    # If we're far below target, hit to get closer
    if current_value <= target - 10:
        return "HIT"
    
    # If we're moderately below target, be more cautious
    if current_value <= target - 5:
        if safe_prob > 0.7:  # 70% chance of safe hit
            return "HIT"
        else:
            return "STAY"
    
    # When very close to target, be very conservative
    if safe_prob > 0.9:  # 90% chance of safe hit
        return "HIT"
    else:
        return "STAY"
