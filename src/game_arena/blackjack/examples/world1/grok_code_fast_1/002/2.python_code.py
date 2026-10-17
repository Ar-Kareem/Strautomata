
def get_value(hand, target):
    total = 0
    has_ace = False
    for card in hand:
        if card == "A":
            has_ace = True
            total += 11
        elif card in ["J", "Q", "K"]:
            total += 10
        else:
            total += int(card)
    if has_ace and total > target:
        total -= 10  # Convert Ace to 1 if needed
    return total

def policy(hand, target):
    v = get_value(hand, target)
    if v >= target:
        return "STAY"  # Already at or beyond target, no point in hitting
    else:
        if target - v <= 3:
            return "STAY"  # Close to target, minimize bust risk
        else:
            return "HIT"  # Too far, hit to get closer
