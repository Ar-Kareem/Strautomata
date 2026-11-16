
import numpy as np
from typing import List, Dict, Tuple

def policy(hand: List[str], target: int) -> str:
    """
    A policy for a simplified Blackjack-like game.
    
    Strategy:
    - Calculate current hand value with Aces counted optimally
    - Use a dynamic strategy based on target value and current hand
    - Be more aggressive when target is high, more conservative when low
    - Use probabilistic model of remaining cards to estimate risk
    """
    
    # Card value mapping
    def card_value(card: str) -> int:
        if card in ["J", "Q", "K"]:
            return 10
        elif card == "A":
            return 11  # Will adjust later if needed
        else:
            return int(card)
    
    # Calculate current hand value with optimal Ace counting
    def hand_value(cards: List[str]) -> int:
        total = 0
        aces = 0
        
        for card in cards:
            if card == "A":
                aces += 1
                total += 11
            else:
                total += card_value(card)
        
        # Adjust Aces from 11 to 1 if needed to avoid busting
        while total > target and aces > 0:
            total -= 10  # Convert an Ace from 11 to 1
            aces -= 1
            
        return total
    
    # Get current hand value
    current_value = hand_value(hand)
    
    # If already at or above target, must stay
    if current_value >= target:
        return "STAY"
    
    # Calculate remaining cards in deck
    all_cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    remaining_cards = [card for card in all_cards if card not in hand]
    
    # Calculate bust probability for next draw
    safe_cards = 0
    for card in remaining_cards:
        value = card_value(card)
        if current_value + (value - 10 if card == "A" and current_value + 11 > target else value) <= target:
            safe_cards += 1
    
    bust_risk = 1.0 - (safe_cards / len(remaining_cards)) if remaining_cards else 1.0
    
    # Distance to target
    distance = target - current_value
    
    # Dynamic threshold based on target and current state
    # For higher targets, we can be more aggressive
    base_threshold = 0.3
    # Adjust threshold based on target (higher targets allow more risk)
    target_factor = (target - 10) / 20  # Normalized 0-1 based on target range
    # Adjust based on distance to target
    distance_factor = min(distance / 5, 1.0)  # Need to get closer if far behind
    # Adjust based on how close we already are (be careful near target)
    proximity_factor = 1.0 - min((target - current_value) / 5, 1.0)
    
    # Final risk tolerance
    risk_tolerance = base_threshold + 0.3 * target_factor + 0.2 * distance_factor - 0.3 * proximity_factor
    
    # Special case: very low hands should always hit
    if current_value <= max(12, target * 0.5):
        return "HIT"
    
    # If we're close to target and risk is high, stay
    if bust_risk > risk_tolerance and distance <= 5:
        return "STAY"
    
    # Conservative play when very close to target
    if distance <= 2:
        return "STAY"
    
    # If we have a good chance of improving without busting, hit
    if bust_risk < 0.5 and distance > 3:
        return "HIT"
    
    # Default: hit if we're far from target
    if distance > 5:
        return "HIT"
    
    # Otherwise stay
    return "STAY"
