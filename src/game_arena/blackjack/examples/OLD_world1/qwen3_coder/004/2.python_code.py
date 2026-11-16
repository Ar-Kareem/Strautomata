
import numpy as np

# Precompute card values
CARD_VALUES = {
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10,
    "J": 10, "Q": 10, "K": 10, "A": 11
}

ALL_CARDS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

def calculate_hand_value(hand):
    """Calculate the best possible value of a hand considering Aces."""
    total = sum(CARD_VALUES[card] for card in hand)
    
    # Adjust for Aces if we're over target
    aces = hand.count("A")
    while total > 0 and aces > 0 and total > 21:
        total -= 10
        aces -= 1
        
    return total

def expected_value_of_hit(current_hand, target, remaining_cards):
    """Calculate the expected value after hitting."""
    current_value = calculate_hand_value(current_hand)
    
    # If we're already at or above target, hitting is risky
    if current_value >= target:
        # Probability of busting if we hit
        bust_probability = 0
        total_cards = len(remaining_cards)
        
        if total_cards == 0:
            return current_value
            
        for card in remaining_cards:
            new_hand = current_hand + [card]
            new_value = calculate_hand_value(new_hand)
            if new_value > target:
                bust_probability += 1
                
        bust_prob = bust_probability / total_cards
        
        # If high chance of busting, it's probably better to stay
        if bust_prob > 0.5:
            return -1000  # Discourage hitting
            
    # Calculate expected value of hitting
    total_value = 0
    valid_hands = 0
    
    for card in remaining_cards:
        new_hand = current_hand + [card]
        new_value = calculate_hand_value(new_hand)
        
        if new_value <= target:
            total_value += new_value
            valid_hands += 1
        # If bust, contribute nothing to expected value
            
    if valid_hands == 0:
        return -1000  # All hits lead to bust
        
    return total_value / len(remaining_cards)

def policy(hand: list[str], target: int) -> str:
    """
    Implement a blackjack policy based on hand value and remaining cards.
    """
    current_value = calculate_hand_value(hand)
    
    # If we've already busted or reached/exceeded target, stay
    if current_value > target:
        return "STAY"
    
    if current_value == target:
        return "STAY"
    
    # Determine which cards we still have available
    hand_counts = {card: hand.count(card) for card in ALL_CARDS}
    remaining_cards = []
    for card in ALL_CARDS:
        max_count = 1  # Only one of each card in our deck
        remaining_count = max_count - hand_counts.get(card, 0)
        remaining_cards.extend([card] * remaining_count)
    
    # If no cards left to draw, must stay
    if not remaining_cards:
        return "STAY"
    
    # Simple threshold-based strategy adjusted by target
    # For low targets, be more conservative
    # For high targets, be more aggressive
    
    # Calculate risk threshold based on how close we are to target
    distance_to_target = target - current_value
    
    # If we're very close to target, be cautious
    if distance_to_target <= 3:
        # Check probability of improving without busting
        safe_cards = 0
        total_cards = len(remaining_cards)
        
        for card in remaining_cards:
            card_value = CARD_VALUES[card]
            # For A, consider it as 1 if that helps
            if card == "A" and current_value + 11 > target:
                card_value = 1
                
            if current_value + card_value <= target:
                safe_cards += 1
                
        safe_probability = safe_cards / total_cards if total_cards > 0 else 0
        
        # Stay if less than 40% chance of safely improving
        if safe_probability < 0.4:
            return "STAY"
    
    # For moderate distances, use a value-based approach
    elif distance_to_target <= 7:
        expected_val = expected_value_of_hit(hand, target, remaining_cards)
        # Stay if expected value of hitting is not significantly better
        if expected_val <= current_value + 1:
            return "STAY"
            
    # For large distances, be more aggressive but still have limits
    else:
        # Don't hit if we're already at a reasonable value
        if current_value >= min(17, target - 3):
            return "STAY"
    
    return "HIT"
