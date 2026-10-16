
import numpy as np

def policy(hand: list[str], target: int) -> str:
    # Define card values (face cards are 10, Ace will be handled separately)
    card_values = {
        "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10,
        "J": 10, "Q": 10, "K": 10
    }
    
    # Count Aces separately and calculate sum without Aces
    ace_count = hand.count("A")
    non_ace_sum = sum(card_values[card] for card in hand if card != "A")
    
    # Calculate optimal hand value (use Aces as 11 if possible, otherwise 1)
    current_sum = non_ace_sum
    for _ in range(ace_count):
        if current_sum + 11 <= target:
            current_sum += 11
        else:
            current_sum += 1
    
    # If we're already at or above target, stay (or would bust on next hit)
    if current_sum >= target:
        return "STAY"
    
    # Calculate threshold for staying
    # Base threshold: target - 3 gives some buffer
    # Make it adaptive based on target size
    threshold = target - max(2, (target - 10) // 4 + 1)
    
    # If we're close enough to target, stay
    if current_sum >= threshold:
        return "STAY"
    
    # If the risk of busting on next hit is very high, stay
    # Estimate minimum value of next card (1 for Ace, but Ace might be used as 11)
    min_next_card = 1  # An Ace can always be counted as 1
    if current_sum + min_next_card > target:
        return "STAY"
    
    # Otherwise, hit
    return "HIT"
