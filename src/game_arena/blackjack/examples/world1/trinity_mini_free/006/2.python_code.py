
def policy(hand: list[str], target: int) -> str:
    S = 0
    A = 0
    for card in hand:
        if card == "A":
            A += 1
        else:
            if card in ["J", "Q", "K"]:
                value = 10
            elif card == "10":
                value = 10
            else:
                value = int(card)
            S += value
    
    current_total = S + A + min(10 * A, max(0, target - S - A))
    
    if current_total < target:
        diff = target - current_total
        if diff <= 5:
            return "HIT"
        else:
            return "STAY"
    else:
        return "STAY"
