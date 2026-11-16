
def policy(hand: list[str], target: int) -> str:
    """
    Implements a Blackjack policy for a target T (10-30) using a 13-card deck.
    """
    
    values_map = {
        "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,
        "10": 10, "J": 10, "Q": 10, "K": 10, "A": 11
    }
    
    def calculate_score(cards):
        score = sum(values_map.get(c, 0) for c in cards)
        # Handle Aces
        num_aces = cards.count("A")
        while score > target and num_aces > 0:
            score -= 10
            num_aces -= 1
        return score

    current_score = calculate_score(hand)
    
    # If we are already at or above target, we must stay (though policy 
    # shouldn't be called if we are at target usually)
    if current_score >= target:
        return "STAY"

    # Identify remaining cards in our specific 13-card deck
    full_deck = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    remaining_deck = full_deck[:]
    for card in hand:
        if card in remaining_deck:
            remaining_deck.remove(card)
            
    if not remaining_deck:
        return "STAY"

    # Simulation check: how many cards would result in a bust?
    bust_count = 0
    for next_card in remaining_deck:
        if calculate_score(hand + [next_card]) > target:
            bust_count += 1
            
    bust_prob = bust_count / len(remaining_deck)
    
    # Strategy Logic:
    # If the probability of busting is less than or equal to 40%, we take the risk.
    # Additionally, if our score is very low relative to target, we should hit anyway.
    # Because target can be up to 30, we are more aggressive at lower scores.
    
    if bust_prob < 0.45:
        return "HIT"
    
    # Aggressiveness adjustment: If target is high and current score is low
    # (e.g., target 30, score 15), we almost always hit.
    if target - current_score > 7:
        return "HIT"

    return "STAY"
