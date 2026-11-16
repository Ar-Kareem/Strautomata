
import numpy as np

def policy(hand: list[str], target: int) -> str:
    # Define card values
    card_values = {
        "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10,
        "J": 10, "Q": 10, "K": 10, "A": 11
    }
    
    # Calculate current hand value with Aces handled properly
    def calculate_hand_value(hand):
        total = 0
        aces = 0
        for card in hand:
            if card == "A":
                aces += 1
            else:
                total += card_values[card]
        
        # Add aces as 11 if possible, otherwise as 1
        for _ in range(aces):
            if total + 11 <= target:
                total += 11
            else:
                total += 1
        return total
    
    current_value = calculate_hand_value(hand)
    
    # If we've already busted or reached target, stay
    if current_value >= target:
        return "STAY"
    
    # Determine which cards we've already used
    all_cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    used_cards = set(hand)
    remaining_cards = [card for card in all_cards if card not in used_cards]
    
    # If no cards left to draw, stay
    if not remaining_cards:
        return "STAY"
    
    # Calculate the probability of improving our hand without busting
    favorable_outcomes = 0
    total_outcomes = len(remaining_cards)
    
    for card in remaining_cards:
        new_hand = hand + [card]
        new_value = calculate_hand_value(new_hand)
        # If drawing this card doesn't bust us, it's favorable
        if new_value <= target:
            favorable_outcomes += 1
    
    # Calculate probability of not busting with next card
    safe_prob = favorable_outcomes / total_outcomes if total_outcomes > 0 else 0
    
    # Calculate expected value if we hit
    expected_value = 0
    if total_outcomes > 0:
        for card in remaining_cards:
            new_hand = hand + [card]
            new_value = calculate_hand_value(new_hand)
            expected_value += new_value
        expected_value /= total_outcomes
    
    # Simple heuristic: 
    # - If we're far from target, hit
    # - If we're close to target and risk busting, stay
    # - Consider the probability of improving our hand
    
    distance_to_target = target - current_value
    
    # If we're very close to target, be more conservative
    if distance_to_target <= 3 and safe_prob < 0.5:
        return "STAY"
    
    # If we're far from target, be more aggressive
    if distance_to_target > 5:
        return "HIT"
    
    # In the middle ground, consider both probability and distance
    # If we have a good chance of improving without busting, hit
    if safe_prob > 0.4:
        return "HIT"
    else:
        return "STAY"
