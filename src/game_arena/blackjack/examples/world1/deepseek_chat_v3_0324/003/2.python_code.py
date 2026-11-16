
import numpy as np

def calculate_hand_value(hand: list[str], target: int) -> int:
    """Calculate the current value of the hand, adjusting Aces as needed."""
    value = 0
    num_aces = 0
    
    # First pass: count all cards except Aces
    for card in hand:
        if card == 'A':
            num_aces += 1
        elif card in ['J', 'Q', 'K']:
            value += 10
        else:  # number cards
            value += int(card)
    
    # Handle Aces
    for _ in range(num_aces):
        # Add 11 if it won't make us exceed target (when possible)
        if value + 11 <= target:
            value += 11
        else:
            value += 1
    
    return value

def policy(hand: list[str], target: int) -> str:
    # All possible cards in the deck
    full_deck = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
    
    # Calculate remaining cards in our deck
    remaining_cards = [card for card in full_deck if card not in hand]
    
    current_value = calculate_hand_value(hand, target)
    
    # If we're at or above target, stay
    if current_value >= target:
        return "STAY"
    
    # Calculate possible outcomes if we hit
    possible_values = []
    for card in remaining_cards:
        if card == 'A':
            # Try both possibilities for Ace
            if current_value + 11 <= target:
                possible_values.append(current_value + 11)
            else:
                possible_values.append(current_value + 1)
        elif card in ['J', 'Q', 'K']:
            possible_values.append(current_value + 10)
        else:
            possible_values.append(current_value + int(card))
    
    # Calculate bust probability
    bust_prob = sum(1 for v in possible_values if v > target) / len(possible_values) if remaining_cards else 0
    
    # Calculate average improvement
    if possible_values:
        avg_improvement = np.mean([min(v, target) for v in possible_values]) - current_value
    else:
        avg_improvement = 0
    
    # Decision making
    if current_value <= target - 5:
        # If we're far below target, be aggressive
        return "HIT"
    elif current_value <= target - 3 and bust_prob < 0.5:
        # Moderate case
        return "HIT"
    elif avg_improvement > 0 and bust_prob < 0.3:
        # Small positive expected value with low bust chance
        return "HIT"
    else:
        return "STAY"
