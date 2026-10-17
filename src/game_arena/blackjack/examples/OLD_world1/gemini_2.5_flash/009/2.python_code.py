
def policy(hand: list[str], target: int) -> str:
    """
    Implements a policy for a simplified Blackjack-like game.

    Args:
        hand: The list of strings representing the cards you currently hold.
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
            # "A" is 11 if current_total + 11 <= target, otherwise 1
            if current_total + 11 <= target_score:
                return 11
            else:
                return 1
        return 0  # Should not happen

    current_score = 0
    num_aces = 0
    for card in hand:
        if card != "A":
            current_score += get_card_value(card, current_score, target)
        else:
            num_aces += 1

    # First, calculate score with all Aces as 11 if possible
    # And then adjust them to 1 if we'd bust
    for _ in range(num_aces):
        if current_score + 11 <= target:
            current_score += 11
        else:
            current_score += 1
            # If an Ace was added as 11 and now we are over target,
            # we need to re-evaluate it as 1.
            # This logic is simpler if we just process all non-aces first
            # then add aces greedily. The above loop does this with adjustment.


    # Let's re-calculate to handle Ace values correctly considering target
    potential_score = 0
    ace_count = 0
    for card in hand:
        if card.isdigit():
            potential_score += int(card)
        elif card in ["J", "Q", "K"]:
            potential_score += 10
        elif card == "A":
            ace_count += 1
    
    # Add aces, initially as 11
    current_score = potential_score
    for _ in range(ace_count):
        current_score += 11

    # Adjust aces from 11 to 1 if busting
    for _ in range(ace_count):
        if current_score > target and current_score - 10 >= 1: # -10 effectively changes an 11 to a 1
            current_score -= 10
        else:
            break # No more aces to adjust, or adjustment won't help


    # If we are already over the target, we bust.
    # While the game rules imply we lose, the policy still needs to return an action.
    # However, in a real game, this state might be terminal. Here we assume we want to avoid it.
    if current_score > target:
        return "STAY"  # Already busted, no point hitting further. But this shouldn't happen usually for decision.

    # If the current score is very close to the target, staying is usually better.
    # The exact threshold can be tuned.
    # Consider the value of the next card. The average value of a card (excluding Ace before its value is fixed)
    # is roughly (2+3+..+10 + 10*3)/12 = (54+30)/12 = 84/12 = 7.
    # With Ace as 1 or 11, it complicates this.
    # A safer assumption is to stay if we are very close to target.

    # This is a simple heuristic. If current score is already >= target, we should have busted or stayed.
    # This check is more about predicting what a "safe" score is.
    
    # If our current score is already quite good and a hit is likely to bust us, stay.
    # A common blackjack strategy is to hit until 17 or higher. Here, we relate it to target.
    # A more aggressive strategy based on probabilities could be implemented.
    
    # Consider what drawing another card might yield.
    # The lowest card is 2. If current_score + 2 > target, then any hit will bust us.
    if current_score + 2 > target:
        return "STAY"

    # If we are very close, say within 2-3 points of the target,
    # hitting is risky.
    # This range is a tunable parameter.
    if target - current_score < 4: # If we are only 1, 2, or 3 away from target
        return "STAY"
    
    # If the target is small, and we already have a decent hand, stay.
    # For example, if target is 15, and we have 14, hitting high cards (10) would bust.
    # If target is large, like 30, and we have 15, hitting is usually good.
    
    # A simple threshold for hitting.
    # If current score is "sufficiently" lower than the target, hit.
    # The "sufficiently" depends on the possibility of busting.
    # Let's say if we are below a certain percentage of the target, we hit.
    
    # Generally, it's safer to hit if there's enough room to safely draw a low card.
    # Let's consider the average card value for decision making.
    # Average card value (excluding Ace's dual nature) is around 7-8.
    
    # If we are very far from the target, hitting is the only way to get closer.
    # If current_score is less than target - (average_card_value + buffer), hit.
    
    # A more robust strategy:
    # 1. If current_score > target: STAY (already busted or equal)
    # 2. If current_score is optimal (equal to target): STAY
    # 3. If current_score + min_card_value (2) > target: STAY (any hit busts) - already covered by +2 > target
    # 4. If current_score is "good enough" and risk of bust is high: STAY
    # 5. Otherwise: HIT
    
    # Let's refine the "good enough" part.
    # The "sweet spot" is target. Getting closer or equal is good.
    
    # If our score is within a certain range of the target, stay.
    # Example: If we are 0, 1, 2 or 3 away from the target, it's generally good to stay.
    # The lowest card value is 2. If target - current_score <= 2, and we hit a 2, we could be perfect or close.
    # But if we hit a 3 or higher, we might bust.
    # If target - current_score == 1 (e.g., hand = 19, target = 20), hitting anything but Ace (1) or J/Q/K (10) as 10 would bust.
    # If hitting leads to a good chance of busting with typical cards, stay.
    
    # Given the simplicity, a threshold-based strategy is effective.
    # Let's try a fixed threshold relative to the target.
    # If current_score is above a certain percentage of the target, stay.
    # Example: if current_score >= target * 0.85
    
    # A more general approach is to "aim" for a score slightly below target,
    # accounting for the possibility of drawing a high card.
    
    # Strategy:
    # If current_score is very close to target, STAY.
    # "Very close" can be defined as current_score >= target - X, where X is a small integer (e.g., 3, 4, 5).
    # If target is small, X should be smaller. If target is large, X can be larger.
    # This suggests X isn't fixed, but relative.

    # Let's use a simpler rule for now: if current score approaches the target, stay.
    # A buffer of 3-4 points seems reasonable for not busting with an average card.
    if current_score >= target - 3:
        return "STAY"
    
    # Special case: If target is very small (e.g., 10-15), we might need to stay earlier.
    # For example, if target is 12, and current_score is 8. target-3 = 9. So we would hit.
    # Hitting could give us 10, bringing us to 18 and bust.
    # For very small targets, be more conservative.
    if target <= 15:
        if current_score >= target - 2: # Reduce buffer for small targets
            return "STAY"

    # Otherwise, hit. We have enough room for more cards.
    return "HIT"

