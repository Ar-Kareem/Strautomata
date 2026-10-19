
def policy(hand: list[str], target: int) -> str:
    # Define the full deck
    ALL_CARDS = {"A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"}
    
    # Helper function to compute the value of a single card (non-Ace)
    def value(card: str) -> int:
        if card in ["J", "Q", "K"]:
            return 10
        elif card == "A":
            return 1  # Aces are handled specially in hand evaluation
        else:
            return int(card)
    
    # Compute current hand value with optimal Ace usage
    count_aces = hand.count("A")
    non_ace_sum = sum(value(card) for card in hand if card != "A")
    base = non_ace_sum + count_aces  # all aces counted as 1
    # How many aces can we upgrade to 11 (i.e., add 10) without exceeding target?
    # Each upgrade adds 10
    max_upgrade = (target - base) // 10
    num_upgraded = min(count_aces, max_upgrade)
    current_value = base + 10 * num_upgraded
    
    # If current value is already >= target, we stay (either at target or bust)
    if current_value >= target:
        return "STAY"
    
    # Calculate needed improvement
    needed = target - current_value
    
    # Get remaining cards
    remaining = ALL_CARDS - set(hand)
    
    # If no cards left, stay
    if not remaining:
        return "STAY"
    
    # Count safe cards: they won't cause a bust when drawn
    safe_count = 0
    for card in remaining:
        if card == "A":
            # Ace can always be used as 1, so it's safe
            safe_count += 1
        else:
            card_val = value(card)
            if current_value + card_val <= target:
                safe_count += 1
    
    safety_prob = safe_count / len(remaining)
    
    # Decision logic based on how close we are to target
    if needed >= 5:
        # We are far from target, so we are willing to take more risk
        return "HIT"
    elif needed >= 2:
        # We are close; require higher safety
        return "HIT" if safety_prob >= 0.7 else "STAY"
    else:
        # needed == 1: very close, only hit if very safe
        return "HIT" if safety_prob >= 0.85 else "STAY"
