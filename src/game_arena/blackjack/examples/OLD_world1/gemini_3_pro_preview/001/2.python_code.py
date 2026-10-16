
import random

def policy(hand: list[str], target: int) -> str:
    """
    Determines whether to 'HIT' or 'STAY' in a simplified Blackjack game.
    
    Strategy:
    1. Calculate current score with simplified Ace logic (maximize score <= target).
    2. Track remaining cards in the finite 13-card deck.
    3. Simulate outcomes of drawing every remaining card.
    4. HIT if:
       - It is impossible to bust (probability of safe draw is 1.0).
       - The probability of not busting exceeds a dynamic threshold based on the gap to the target.
       - Hitting offers a chance to improve the score (handles specific Soft Ace edge cases).
    """
    
    # Define card values
    # A is handled dynamically; J, Q, K are 10.
    values = {
        "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,
        "10": 10, "J": 10, "Q": 10, "K": 10, "A": 11
    }

    def calculate_score(cards, t):
        """Calculates the best valid score <= t. If all valid interpretations > t, returns the lowest score (bust)."""
        current_sum = 0
        aces = 0
        
        # Sum fixed values
        for c in cards:
            if c == "A":
                aces += 1
            else:
                current_sum += values[c]
        
        # Add Aces as 1s initially
        current_sum += aces
        
        # Try to upgrade Aces to 11 (add 10) as long as we don't exceed t
        # We can upgrade at most `aces` times
        for _ in range(aces):
            if current_sum + 10 <= t:
                current_sum += 10
            else:
                break
        
        return current_sum

    current_score = calculate_score(hand, target)

    # 1. Forced Stay Condition
    # If we've already reached or exceeded the target, we stop.
    if current_score >= target:
        return "STAY"

    # 2. Determine Remaining Deck
    # Full deck contains one of each rank. We remove cards currently in hand.
    full_deck = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    remaining_deck = list(full_deck)
    
    for card in hand:
        if card in remaining_deck:
            remaining_deck.remove(card)
            
    if not remaining_deck:
        return "STAY"

    # 3. Simulate Next Draw
    safe_draws = 0
    improving_draws = 0
    total_card_count = len(remaining_deck)
    
    for card in remaining_deck:
        new_score = calculate_score(hand + [card], target)
        
        if new_score <= target:
            safe_draws += 1
            if new_score > current_score:
                improving_draws += 1
                
    prob_safe = safe_draws / total_card_count if total_card_count > 0 else 0.0

    # 4. Decision Logic
    
    # A. Detect 'Soft Collapse': If we have a soft hand (e.g., Ace=11, Total=11, Target=12),
    #    drawing a low card (e.g., 2) forces Ace to 1, reducing score to 3.
    #    If no draw can actually increase our score, we should strictly STAY.
    if improving_draws == 0:
        return "STAY"

    # B. Free Hit: If there is 0% chance of busting, always Hit to attempt improvement.
    if prob_safe == 1.0:
        return "HIT"

    # C. Risk Threshold:
    #    Calculate a required safety probability based on how close we are to the target.
    #    Gap = Target - Current.
    #    - Large Gap (e.g., 10): Low threshold (Aggressive).
    #    - Small Gap (e.g., 2): High threshold (Conservative).
    
    gap = target - current_score
    
    # Heuristic: Start at 0.95 requirement for gap=0, decrease by 0.10 per point of gap.
    # Gap 10 -> Threshold -0.05 (Hit if prob_safe > 0, practically always).
    # Gap 5  -> Threshold 0.45 (Hit if prob_safe > 45%).
    # Gap 1  -> Threshold 0.85 (Hit only if very safe).
    threshold = 0.95 - (gap * 0.10)
    
    if prob_safe > threshold:
        return "HIT"
        
    return "STAY"
