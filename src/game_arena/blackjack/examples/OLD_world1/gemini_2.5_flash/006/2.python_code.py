
def policy(hand: list[str], target: int) -> str:
    """
    Implements a policy for a simplified Blackjack-like game.

    Args:
        hand: A list of strings representing the cards you currently hold.
        target: The integer T you are trying to approach.

    Returns:
        One of the two actions as a string: "HIT" or "STAY".
    """

    def get_card_value(card: str, current_total: int, target_score: int) -> int:
        if card.isdigit():
            return int(card)
        elif card in ["J", "Q", "K"]:
            return 10
        elif card == "A":
            # Ace is 11 unless it makes the hand bust or go far over the target
            # In this simplified game, we prioritize staying under target and not busting.
            # If 11 busts, it should be 1. Otherwise, 11 is preferred.
            if current_total + 11 > target_score:
                return 1
            else:
                return 11
        return 0  # Should not happen

    def calculate_hand_value(current_hand: list[str], target_score: int) -> int:
        # Calculate initial sum, treating Aces as 11 for now
        temp_sum = 0
        num_aces = 0
        for card in current_hand:
            if card.isdigit():
                temp_sum += int(card)
            elif card in ["J", "Q", "K"]:
                temp_sum += 10
            elif card == "A":
                temp_sum += 11
                num_aces += 1

        # Adjust Aces if the sum busts
        while temp_sum > target_score and num_aces > 0:
            temp_sum -= 10  # Change an Ace from 11 to 1
            num_aces -= 1

        return temp_sum

    current_score = calculate_hand_value(hand, target)

    # If busting, we've already lost, but the game expects a decision. We'll stay as we can't un-bust.
    if current_score > target:
        return "STAY"

    # Strategy:
    # Always hit if current score is low, as long as it's unlikely to bust.
    # The threshold for hitting should depend on the target.
    # We want to get as close to the target as possible without going over.

    # If the current score is already very close to the target, stay.
    # The buffer for staying should be relative to the target.
    # For a target of 10-30, a buffer of 2-5 seems reasonable.

    # Example threshold: If current score is >= target - 4, stay.
    # This tries to maximize the chance of getting a score close to target
    # without taking too much risk.
    
    # Consider what cards are left if we hit. The lowest possible card value is 1 (Ace adjusted) or 2.
    # The highest is 11 (Ace) or 10.

    # Basic strategy:
    # If we are already very close to the target, stay.
    if current_score >= target - 3: # A bit more aggressive for higher targets
        return "STAY"
    
    # Or, if we are at a point where a hit could easily bust us, stay.
    # Let's consider the worst case: drawing a 10 (or J, Q, K).
    # If current_score + 10 would bust, then we should be very cautious.
    if current_score + 10 > target:
        # We need to be more nuanced here.
        # If adding 10 busts, but adding 2 doesn't, we might still hit.
        # Let's consider getting closer.
        
        # If we are almost sure to bust even with a small card, then stay.
        # This implies our current_score is already high (e.g., target - 1, target - 2, target - 3)
        # We've already handled current_score >= target - 3 with an immediate STAY.
        
        # If current_score + 10 > target, but current_score + 2 <= target:
        # What's the risk of hitting? Drawing a 10, J, Q, K is 4/13 chance.
        # Drawing an A that values as 11 is also significant.
        
        # Let's simplify for now: Stay if a 10 would bust us, and our score is already somewhat decent.
        # Refined rule: If score is above target - 7 (e.g., 23 for a target of 30), and adding 10 busts.
        if current_score >= target - 6: # More conservative as we get closer
            return "STAY"

    # Otherwise, hit. We still have room to improve.
    return "HIT"

