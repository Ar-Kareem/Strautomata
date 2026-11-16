
def policy(hand: list[str], target: int) -> str:
    """
    Determines whether to HIT or STAY in a Blackjack-like game with a variable target.
    """
    # Map ranks to their primary values
    values_map = {
        "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,
        "10": 10, "J": 10, "Q": 10, "K": 10, "A": 11
    }
    
    def calculate_score(current_hand):
        score = sum(values_map[card] for card in current_hand)
        aces = current_hand.count("A")
        # Adjust Aces from 11 to 1 if we are over the target
        while score > target and aces > 0:
            score -= 10
            aces -= 1
        return score

    current_score = calculate_score(hand)
    
    # If we are already at or above target (though game should end if above), stay
    if current_score >= target:
        return "STAY"
    
    # Identify cards remaining in our 13-card deck
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
        if calculate_score(hand + [next_card]) > target:
            bust_count += 1
            
    prob_bust = bust_count / len(remaining_deck)
    
    # Strategy: 
    # 1. If we can't possibly bust, always HIT.
    if bust_count == 0:
        return "HIT"
    
    # 2. If the target is high, we need to be more aggressive.
    # 3. If the score is close to the target, and bust risk is significant, STAY.
    
    # Threshold logic:
    # If target is large (e.g. 30), a score of 20 is not "good". 
    # We want to be within a certain distance of the target.
    distance_to_target = target - current_score
    
    # Risk tolerance: if the distance to target is small, we are more likely to stay.
    # If we are within 4 points of the target, and the chance of busting is over 40%, stay.
    if distance_to_target <= 3:
        if prob_bust > 0.3:
            return "STAY"
    
    if distance_to_target <= 5:
        if prob_bust > 0.5:
            return "STAY"

    # Default to staying if bust probability is high
    if prob_bust > 0.7:
        return "STAY"

    return "HIT"
