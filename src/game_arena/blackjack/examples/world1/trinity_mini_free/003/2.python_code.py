
def policy(hand: list[str], target: int) -> str:
    total = 0
    aces = 0
    for card in hand:
        if card == 'A':
            aces += 1
        elif card in ['J', 'Q', 'K']:
            total += 10
        else:
            total += int(card)
    
    # Handle Aces: one Ace only
    if aces == 1:
        if total + 11 <= target:
            total += 11
        else:
            total += 1
    elif aces > 1:
        total += aces  # Fallback for multiple Aces (though not possible)
    
    # Bust check
    if total > target:
        return "STAY"
    
    # Decision: hit if gap >10, else stay
    if total < target:
        return "HIT" if total < target - 10 else "STAY"
    return "STAY"
