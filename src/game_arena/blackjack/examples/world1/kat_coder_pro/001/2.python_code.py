
import numpy as np

def policy(hand: list[str], target: int) -> str:
    # Card values mapping
    card_values = {
        '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
        'J': 10, 'Q': 10, 'K': 10, 'A': 11
    }
    
    # Calculate current hand value with Ace logic
    def get_hand_value(hand):
        # Count Aces separately
        aces = hand.count('A')
        non_ace_value = sum(card_values[card] for card in hand if card != 'A')
        
        # Try to use Aces as 11 first, then as 1 if needed
        current_value = non_ace_value
        for _ in range(aces):
            if current_value + 11 <= target:
                current_value += 11
            else:
                current_value += 1
        return current_value
    
    current_value = get_hand_value(hand)
    
    # If already at or over target, must stay
    if current_value >= target:
        return "STAY"
    
    # Calculate remaining cards
    all_cards = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
    remaining_cards = [card for card in all_cards if card not in hand]
    
    # If no cards left, must stay
    if not remaining_cards:
        return "STAY"
    
    # Calculate distance to target
    distance = target - current_value
    
    # If very close to target, be conservative
    if distance <= 2:
        return "STAY"
    
    # Calculate risk of busting
    bust_threshold = target - current_value
    bust_cards = [card for card in remaining_cards if card_values[card] > bust_threshold]
    
    # Special handling for Ace - it can be 1 or 11
    # If Ace would cause bust as 11, it becomes 1, so it never causes bust
    bust_probability = len(bust_cards) / len(remaining_cards)
    
    # If high risk of busting, be conservative
    if bust_probability > 0.5:
        return "STAY"
    
    # Calculate expected value if we hit
    # For Ace, we need special handling since it can be 1 or 11
    expected_gain = 0
    for card in remaining_cards:
        if card == 'A':
            # Ace can be 11 if it doesn't bust, otherwise 1
            if current_value + 11 <= target:
                expected_gain += 11
            else:
                expected_gain += 1
        else:
            expected_gain += card_values[card]
    
    expected_gain /= len(remaining_cards)
    
    # If expected gain is high relative to risk, hit
    # Use a threshold that gets more conservative as we get closer to target
    conservative_factor = 1.0 - (current_value / target) * 0.5
    
    if expected_gain > (distance * conservative_factor):
        return "HIT"
    else:
        return "STAY"
