
import math

def policy(hand: list[str], target: int) -> str:
    """
    Implements a policy for a Blackjack-like game with a dynamic target T.
    """
    card_values_map = {
        "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,
        "10": 10, "J": 10, "Q": 10, "K": 10, "A": 11
    }
    
    deck = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    
    def get_hand_value(current_hand):
        value = 0
        aces = 0
        for card in current_hand:
            if card == "A":
                aces += 1
            value += card_values_map[card]
        
        while value > target and aces > 0:
            value -= 10
            aces -= 1
        return value

    current_value = get_hand_value(hand)
    
    # If we are already at or over target, we must stay
    if current_value >= target:
        return "STAY"

    # Identify remaining cards in our specific 13-card deck
    remaining_cards = deck.copy()
    for card in hand:
        if card in remaining_cards:
            remaining_cards.remove(card)
    
    if not remaining_cards:
        return "STAY"

    # Calculate probability of busting
    bust_count = 0
    for card in remaining_cards:
        # Simulate drawing this card
        temp_hand = hand + [card]
        if get_hand_value(temp_hand) > target:
            bust_count += 1
    
    prob_bust = bust_count / len(remaining_cards)
    
    # Heuristic: If probability of busting is > 50%, STAY.
    # Also, if we are within a small margin of the target, stay to avoid the high density of 10-value cards.
    # Usually, scores of T-1, T-2, T-3 are very strong.
    if current_value >= target - 3:
        # High risk of busting since 10/13 cards are usually > 3
        return "STAY"
    
    if prob_bust > 0.5:
        return "STAY"
    
    return "HIT"

