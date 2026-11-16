
def policy(hand: list[str], target: int) -> str:
    # Calculate the current value of the hand, adjusting Aces as needed
    value = 0
    num_aces = 0
    
    for card in hand:
        if card == "A":
            num_aces += 1
        elif card in {"J", "Q", "K"}:
            value += 10
        else:
            value += int(card)
    
    # Adjust Aces: start by counting them as 11, then reduce to 1 if needed
    for _ in range(num_aces):
        if value + 11 <= target:
            value += 11
        else:
            value += 1
    
    # Decide whether to hit or stay
    if value >= target:
        return "STAY"
    else:
        # Hit if the value is significantly below the target, otherwise stay
        # Threshold can be adjusted based on target
        if value <= target - 5:
            return "HIT"
        else:
            return "STAY"
