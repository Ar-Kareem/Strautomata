
def get_hand_value(hand: list[str], target: int) -> int:
    value = 0
    aces = 0
    card_map = {
        "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,
        "10": 10, "J": 10, "Q": 10, "K": 10, "A": 11
    }
    
    for card in hand:
        value += card_map[card]
        if card == "A":
            aces += 1
            
    while value > target and aces > 0:
        value -= 10
        aces -= 1
        
    return value

def policy(hand: list[str], target: int) -> str:
    """
    Implements a Blackjack policy optimized for a variable target T.
    The policy calculates the current hand value and hits if the risk 
    of busting is statistically acceptable given the target.
    """
    # 1. Calculate current hand value
    current_value = get_hand_value(hand, target)
    
    # 2. Identify remaining cards in the 13-card deck
    full_deck = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    remaining_deck = full_deck.copy()
    for card in hand:
        if card in remaining_deck:
            remaining_deck.remove(card)
            
    if not remaining_deck:
        return "STAY"

    # 3. Decision Logic
    # If we are already at or above target (though game should end if above)
    if current_value >= target:
        return "STAY"
    
    # Calculate how many cards in the remaining deck would cause a bust
    bust_count = 0
    for card in remaining_deck:
        temp_hand = hand + [card]
        if get_hand_value(temp_hand, target) > target:
            bust_count += 1
            
    bust_prob = bust_count / len(remaining_deck)
    
    # Heuristic: If target is high, we can afford more risk.
    # If target is low, we must be more conservative.
    # Standard threshold: Stay if bust probability exceeds 35-45% 
    # or if we are within a small margin of the target.
    
    # Calculate margin
    margin = target - current_value
    
    # If target is large (e.g. 30), a score of 26 is like 17 in standard blackjack.
    # If target is small (e.g. 10), 9 is very strong.
    if margin <= 2:
        return "STAY"
    
    if bust_prob > 0.45:
        # If the risk of busting is high, only hit if our score is very low
        if margin > 7:
            return "HIT"
        else:
            return "STAY"
            
    return "HIT"

