
import numpy as np

def policy(hand: list[str], target: int) -> str:
    """
    Blackjack-like policy that balances risk of busting vs potential gain.
    
    Strategy:
    - If current hand value is already above target, STAY (but we should have busted already)
    - If we're very close to target (within 1-2), STAY to avoid busting
    - Use dynamic threshold based on how much room we have
    - Consider the value of an Ace flexibly
    """
    
    def calculate_hand_value(cards):
        """Calculate hand value with flexible Ace (11 or 1)"""
        value = 0
        aces = 0
        
        for card in cards:
            if card in ["J", "Q", "K"]:
                value += 10
            elif card == "A":
                aces += 1
            else:
                value += int(card)
        
        # Add Aces: use 11 if it doesn't cause bust, otherwise 1
        for _ in range(aces):
            if value + 11 <= target:
                value += 11
            else:
                value += 1
                
        return value
    
    def cards_remaining_value_potential():
        """Estimate potential value from remaining cards"""
        all_cards = set(["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"])
        hand_set = set(hand)
        remaining = all_cards - hand_set
        
        # Calculate expected value of next card
        total_val = 0
        count = 0
        for card in remaining:
            if card in ["J", "Q", "K"]:
                total_val += 10
            elif card == "A":
                # Ace can be 11 or 1 - assume 11 if beneficial
                total_val += 11
            else:
                total_val += int(card)
            count += 1
            
        return total_val / count if count > 0 else 0
    
    # Calculate current hand value
    current_value = calculate_hand_value(hand)
    
    # If already at or above target, stay
    if current_value >= target:
        return "STAY"
    
    # How much room do we have?
    room = target - current_value
    
    # If very close to target, stay to avoid busting
    if room <= 2:
        return "STAY"
    
    # Estimate expected value of next card
    expected_next_value = cards_remaining_value_potential()
    
    # Adjust threshold based on risk
    # The closer we are to busting, the more conservative we should be
    bust_risk = 1.0 - (room / 10.0)  # Higher bust risk when room is small
    
    # If we have a lot of room, be more aggressive
    if room >= 8:
        return "HIT"
    
    # Medium room - base decision on expected improvement
    if expected_next_value >= room * 0.7:
        return "HIT"
    
    # Conservative approach when risk is high
    if bust_risk > 0.5 and expected_next_value < room:
        return "STAY"
    
    # Default to HIT if we're far from target
    if current_value < target * 0.7:
        return "HIT"
    
    # Otherwise stay
    return "STAY"
