
import numpy as np
from typing import List, Dict, Tuple

def policy(hand: List[str], target: int) -> str:
    """
    A policy for a simplified Blackjack-like game.
    
    The strategy uses a combination of:
    - Risk-averse hitting when far from target
    - Aggressive staying when close to target
    - Special handling of Aces
    - Probabilistic model of remaining cards
    """
    
    # Card value mapping
    def get_card_value(card: str, current_total: int) -> int:
        if card in ["J", "Q", "K"]:
            return 10
        elif card == "A":
            # Ace is 11 if it doesn't bust us, otherwise 1
            if current_total + 11 <= target:
                return 11
            else:
                return 1
        else:
            return int(card)
    
    # Calculate current hand value
    def calculate_hand_value(hand_cards: List[str]) -> int:
        total = 0
        aces = 0
        
        for card in hand_cards:
            if card == "A":
                aces += 1
            else:
                total += get_card_value(card, total)
        
        # Add aces optimally
        for _ in range(aces):
            if total + 11 <= target:
                total += 11
            else:
                total += 1
                
        return total
    
    # Get all cards
    all_cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    
    # Determine which cards have been used
    used_cards = set(hand)
    remaining_cards = [card for card in all_cards if card not in used_cards]
    
    current_value = calculate_hand_value(hand)
    
    # If we're already at or very close to target, stay
    if current_value >= target:
        return "STAY"
    
    distance_from_target = target - current_value
    
    # If we're busting with any card, stay
    # Find minimum card value we have left
    if remaining_cards:
        min_possible_card = min([get_card_value(card, current_value) for card in remaining_cards])
        if current_value + min_possible_card > target:
            return "STAY"
    
    # Automatic stay conditions
    if distance_from_target == 0:  # Exactly at target
        return "STAY"
    elif current_value > target:  # Already bust
        return "STAY"
    elif distance_from_target <= 2:  # Very close to target
        return "STAY"
    
    # Estimate risk of busting with next card
    safe_cards = 0
    total_remaining = len(remaining_cards)
    
    if total_remaining == 0:
        return "STAY"  # No cards left to draw
    
    for card in remaining_cards:
        card_value = get_card_value(card, current_value)
        if current_value + card_value <= target:
            safe_cards += 1
    
    bust_probability = 1.0 - (safe_cards / total_remaining)
    
    # Decision logic based on distance and risk
    if distance_from_target >= 10:
        # We're far from target, be aggressive
        return "HIT"
    elif distance_from_target >= 6:
        # Moderate distance, hit if risk isn't too high
        if bust_probability < 0.5:
            return "HIT"
        else:
            return "STAY"
    elif distance_from_target >= 3:
        # Close to target, be conservative
        if bust_probability < 0.3:
            return "HIT"
        else:
            return "STAY"
    else:
        # Very close to target, only hit if very safe
        if bust_probability < 0.1:
            return "HIT"
        else:
            return "STAY"
