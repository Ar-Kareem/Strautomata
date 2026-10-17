
def policy(hand: list[str], target: int) -> str:
    # Map card values
    def card_value(card):
        if card in ["J", "Q", "K"]:
            return 10
        elif card == "A":
            return 11
        else:
            return int(card)
    
    # Calculate best possible hand value considering ace flexibility
    total = 0
    ace_count = hand.count("A")
    non_ace_total = 0
    
    for card in hand:
        if card == "A":
            continue
        non_ace_total += card_value(card)
    
    # Try to use aces as 11 first, then downgrade if needed
    best_total = non_ace_total
    aces_used_as_11 = 0
    
    # Use as many aces as 11 as possible without busting
    for _ in range(ace_count):
        if best_total + 11 <= target:
            best_total += 11
            aces_used_as_11 += 1
        else:
            best_total += 1
    
    # If we bust even with all aces as 1, we're busted but still must return stay
    if best_total > target:
        return "STAY"
    
    # We are not busted, decide hit or stay
    # If we are very close to target, stay
    if best_total >= target - 3:
        return "STAY"
    
    # If we are far from target, hit
    if best_total < target - 5:
        return "HIT"
    
    # For values in [target - 4, target - 6], use a risk-aware heuristic
    # Calculate the probability of improving without busting
    # We know which cards we've drawn, so remaining are 13 - len(hand)
    drawn_cards = set(hand)
    remaining_cards = [c for c in ["A","2","3","4","5","6","7","8","9","10","J","Q","K"] if c not in drawn_cards]
    
    # Count how many cards we can draw without busting
    safe_cards = 0
    for card in remaining_cards:
        val = card_value(card)
        # With current best_total, if we add val, can we stay under or equal target?
        # But note: aces can be flexible! So if card is A, we can use it as 1 even if 11 would bust
        if card == "A":
            # Ace can be used as 1 or 11. We need to see if best_total + 1 <= target
            # Since we are trying to maximize, the ace will always be used optimally
            if best_total + 1 <= target:
                safe_cards += 1
        else:
            if best_total + val <= target:
                safe_cards += 1
    
    # If more than half of remaining cards are safe, hit
    if len(remaining_cards) > 0 and safe_cards / len(remaining_cards) > 0.5:
        return "HIT"
    else:
        return "STAY"
