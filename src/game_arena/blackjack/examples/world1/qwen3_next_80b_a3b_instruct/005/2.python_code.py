
import numpy as np

def policy(hand: list[str], target: int) -> str:
    # Card values mapping
    card_values = {
        "A": 11, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, 
        "7": 7, "8": 8, "9": 9, "10": 10, "J": 10, "Q": 10, "K": 10
    }
    
    # All cards in the standard deck
    all_cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    
    # Determine which cards are still in the deck (not in hand)
    remaining_cards = [card for card in all_cards if card not in hand]
    
    # Calculate current hand value with optimal Ace usage
    def calculate_optimal_value(cards):
        # Count Aces and sum non-Ace cards
        non_ace_sum = sum(card_values[card] for card in cards if card != "A")
        num_aces = cards.count("A")
        
        # Try using as many Aces as 11 as possible without busting
        # Start with all Aces as 11, then reduce one by one if needed
        total = non_ace_sum + num_aces * 11
        
        # If total exceeds target, convert Aces from 11 to 1 one by one
        while total > target and num_aces > 0:
            total -= 10  # convert one Ace from 11 to 1
            num_aces -= 1
            
        return total
    
    current_value = calculate_optimal_value(hand)
    
    # If already busted, must stay (though game would end, but policy must return stay)
    if current_value > target:
        return "STAY"
    
    # If very close to target, stay to avoid risk
    if current_value >= target - 2:
        return "STAY"
    
    # If far from target, hit aggressively
    if current_value <= target - 10:
        return "HIT"
    
    # For intermediate range: target - 10 < current_value < target - 3
    # Calculate probability that next card doesn't cause bust
    safe_cards = []
    for card in remaining_cards:
        card_val = card_values[card]
        # Calculate new value if we draw this card
        new_hand = hand + [card]
        new_value = calculate_optimal_value(new_hand)
        
        if new_value <= target:
            safe_cards.append(card)
    
    safe_prob = len(safe_cards) / len(remaining_cards) if remaining_cards else 0
    
    # We'll HIT if probability of staying safe is > 50%, otherwise STAY
    # This gives us a balance: when we have good chance to improve safely, we hit
    if safe_prob > 0.5:
        return "HIT"
    else:
        return "STAY"
