
import collections

def get_hand_value(hand: list[str]) -> int:
    """Calculates the best possible value for a given hand."""
    value = 0
    aces = 0
    card_map = {
        "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,
        "10": 10, "J": 10, "Q": 10, "K": 10, "A": 11
    }
    
    for card in hand:
        if card == "A":
            aces += 1
        value += card_map[card]
        
    while value > 0 and aces > 0:
        # If we have a bust and an ace is counted as 11, reduce it to 1
        # This is handled until we are under target or out of aces.
        # However, the rule says Ace is 1 if total > T.
        # The function logic is slightly different: we return the minimum 
        # because the policy caller knows the Target. 
        # Wait, the rule says Ace is 1 if total > T. Let's adjust.
        # This logic is handled dynamically in the policy.
        break 
    return value, aces

def calculate_score(hand: list[str], target: int) -> int:
    """Calculates the hand value specifically for the given target."""
    val, aces = get_hand_value(hand)
    while val > target and aces > 0:
        val -= 10
        aces -= 1
    return val

def policy(hand: list[str], target: int) -> str:
    current_score = calculate_score(hand, target)
    
    # If we are already at or above target, no reason to hit.
    if current_score >= target:
        return "STAY"
    
    # Identify remaining cards in our deck
    full_deck = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    for card in hand:
        if card in full_deck:
            full_deck.remove(card)
            
    # Calculate probability of busting if we HIT
    safe_cards = 0
    total_remaining = len(full_deck)
    
    for card in full_deck:
        temp_hand = hand + [card]
        if calculate_score(temp_hand, target) <= target:
            safe_cards += 1
            
    prob_safe = safe_cards / total_remaining if total_remaining > 0 else 0
    
    # Heuristic: Hit if the probability of not busting is high.
    # Also Hit if the value is very low, as staying at 10 vs target 25 is a loss.
    if current_score < (target - 5):
        return "HIT"
    
    if prob_safe >= 0.5:
        return "HIT"
    
    return "STAY"

