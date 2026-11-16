
import random

def policy(hand: list[str], target: int) -> str:
    # Define card values
    card_values = {
        "A": 11,
        "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10,
        "J": 10, "Q": 10, "K": 10
    }

    # Calculate current hand value
    def hand_value(hand):
        total = 0
        aces = 0
        
        for card in hand:
            if card == "A":
                aces += 1
                total += 11
            else:
                total += card_values[card]
        
        # Adjust Aces value if needed
        while total > target and aces > 0:
            total -= 10  # Convert Ace from 11 to 1
            aces -= 1
            
        return total
        
    current_value = hand_value(hand)
    
    # If already at or above target, stay
    if current_value >= target:
        return "STAY"
        
    # Calculate remaining cards
    all_cards = set(["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"])
    remaining_cards = list(all_cards - set(hand))
    
    # Simulate draws to estimate bust probability
    bust_count = 0
    simulations = 1000
    
    for _ in range(simulations):
        # Pick a random remaining card
        next_card = random.choice(remaining_cards)
        
        # Calculate potential new hand value
        potential_value = current_value + card_values[next_card]
        
        # Adjust for Ace if needed
        if next_card == "A" and potential_value > target:
            potential_value -= 10
            
        # Check if this would bust
        if potential_value > target:
            bust_count += 1
    
    bust_probability = bust_count / simulations
    
    # Decision logic
    if current_value <= target - 10:
        # Always hit if far from target
        return "HIT"
    elif current_value <= target - 5:
        # Hit if bust probability is low
        if bust_probability < 0.3:
            return "HIT"
        else:
            return "STAY"
    else:
        # Close to target, be more conservative
        if bust_probability < 0.1:
            return "HIT"
        else:
            return "STAY"
