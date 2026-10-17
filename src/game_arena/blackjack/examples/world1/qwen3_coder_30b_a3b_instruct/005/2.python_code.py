
def policy(hand: list[str], target: int) -> str:
    # Calculate current hand value with proper Ace evaluation
    total = 0
    num_aces = 0
    
    for card in hand:
        if card in ["J", "Q", "K"]:
            total += 10
        elif card == "A":
            num_aces += 1
            total += 11  # Start by counting A as 11
        else:
            total += int(card)
    
    # Adjust for Aces if total exceeds target
    while total > target and num_aces > 0:
        total -= 10  # Convert one Ace from 11 to 1
        num_aces -= 1
    
    # If our current hand value is greater than or equal to target,
    # we're either at or over the limit, so we should avoid busting
    if total >= target:
        return "STAY"
    else:
        return "HIT"
