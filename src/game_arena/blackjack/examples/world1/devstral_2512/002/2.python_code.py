
def calculate_hand_value(hand: list[str], target: int) -> int:
    value = 0
    aces = 0
    for card in hand:
        if card == "A":
            value += 11
            aces += 1
        elif card in ["J", "Q", "K"]:
            value += 10
        else:
            value += int(card)
    while value > target and aces > 0:
        value -= 10
        aces -= 1
    return value

def policy(hand: list[str], target: int) -> str:
    current_value = calculate_hand_value(hand, target)
    if current_value >= target:
        return "STAY"
    # Define a threshold to decide when to stay
    # For example, if current_value is within 2 points of target, stay
    if current_value >= target - 2:
        return "STAY"
    else:
        return "HIT"
