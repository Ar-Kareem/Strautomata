
import collections

def policy(hand: list[str], target: int) -> str:
    """
    Implements a policy for a simplified Blackjack game.
    Target T is variable between 10 and 30.
    """
    
    def get_hand_value(cards):
        value = 0
        aces = 0
        card_map = {
            "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,
            "10": 10, "J": 10, "Q": 10, "K": 10, "A": 11
        }
        for card in cards:
            if card == "A":
                aces += 1
            value += card_map[card]
        
        while value > target and aces > 0:
            value -= 10
            aces -= 1
        return value

    # Current state
    current_value = get_hand_value(hand)
    
    # If we are already at or over target, we must stay (or we've already lost)
    if current_value >= target:
        return "STAY"

    # Identify remaining cards in our specific 13-card deck
    full_deck = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    remaining_deck = full_deck.copy()
    for card in hand:
        if card in remaining_deck:
            remaining_deck.remove(card)
            
    if not remaining_deck:
        return "STAY"

    # Calculate the probability of busting if we HIT
    bust_count = 0
    for next_card in remaining_deck:
        if get_hand_value(hand + [next_card]) > target:
            bust_count += 1
            
    bust_prob = bust_count / len(remaining_deck)
    
    # Strategy:
    # 1. If we can't bust, always HIT.
    if bust_count == 0:
        return "HIT"
    
    # 2. If the current value is quite low relative to target, 
    # and risk is acceptable, HIT.
    # We use a threshold: if risk of busting is > 40%, we stay.
    # Also, if we are within 2 points of target, we stay.
    if current_value >= target - 2:
        return "STAY"
        
    if bust_prob > 0.45:
        return "STAY"
        
    return "HIT"
