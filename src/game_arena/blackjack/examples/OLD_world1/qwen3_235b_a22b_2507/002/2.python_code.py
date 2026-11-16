
import numpy as np
from typing import List

def policy(hand: List[str], target: int) -> str:
    """
    A blackjack-like policy that balances risk of busting with the need to approach the target.
    
    Strategy:
    - Calculate current hand value with optimal Ace handling
    - Use a dynamic threshold based on distance to target and risk tolerance
    - Consider probability of busting with next card
    """
    
    def get_hand_value(hand: List[str]) -> int:
        """Calculate hand value with Aces counting as 11 if possible, otherwise 1"""
        value = 0
        aces = 0
        
        for card in hand:
            if card == "A":
                aces += 1
                value += 11
            elif card in ["J", "Q", "K"]:
                value += 10
            else:
                value += int(card)
        
        # Adjust Aces from 11 to 1 if needed to avoid busting
        while value > target and aces > 0:
            value -= 10  # Change Ace from 11 to 1
            aces -= 1
            
        return value
    
    def probability_of_busting(current_value: int, target: int) -> float:
        """Estimate probability of busting if we hit"""
        if current_value >= target:
            return 1.0
            
        safe_threshold = target - current_value
        safe_cards = 0
        total_remaining = 13 - len(hand)  # We draw from fresh deck each time in this game
        
        # Count how many cards would keep us safe
        for card in ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]:
            if card == "A":
                # Ace can be 1 or 11, so if 1 won't bust us, it's safe
                if 1 <= safe_threshold:
                    safe_cards += 1
            elif card in ["J", "Q", "K"]:
                if 10 <= safe_threshold:
                    safe_cards += 1
            else:
                if int(card) <= safe_threshold:
                    safe_cards += 1
                    
        return 1.0 - (safe_cards / 13)  # Using 13 since we have full deck each draw
    
    current_value = get_hand_value(hand)
    
    # If we're already at or above target, always stay
    if current_value >= target:
        return "STAY"
    
    # Calculate how close we are to target
    distance_to_target = target - current_value
    
    # Calculate bust risk
    bust_prob = probability_of_busting(current_value, target)
    
    # Dynamic decision making based on distance and risk
    if distance_to_target == 0:
        return "STAY"
    elif distance_to_target == 1:
        # Very risky to hit, only do so if we're likely to lose by staying
        return "STAY"
    elif distance_to_target <= 3:
        # Close to target, only hit if low bust risk
        if bust_prob < 0.3:
            return "HIT"
        else:
            return "STAY"
    elif distance_to_target <= 6:
        # Moderate distance, hit if reasonable chance of success
        if bust_prob < 0.6:
            return "HIT"
        else:
            return "STAY"
    else:
        # Far from target, need to hit
        # But don't hit if we'd almost certainly bust
        if bust_prob < 0.9:
            return "HIT"
        else:
            return "STAY"
