
def calculate_hand_value(hand):
    value = 0
    aces = 0
    
    for card in hand:
        if card in ["J", "Q", "K"]:
            value += 10
        elif card == "A":
            aces += 1
        else:
            value += int(card)

    for _ in range(aces):
        if value + 11 <= target:
            value += 11
        else:
            value += 1

    return value

def policy(hand: list[str], target: int) -> str:
    hand_value = calculate_hand_value(hand)

    if hand_value < target - 2:  # If significantly less than target
        return "HIT"
    elif hand_value >= target:  # If it's equal to or over target
        return "STAY"
    else:  # Close enough to target, play conservatively
        return "STAY"
