
def policy(hand: list[str], target: int) -> str:
    # Calculate the current hand value
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

    # Adjust for Aces if the hand value exceeds the target
    while value > target and aces > 0:
        value -= 10
        aces -= 1

    # Define a threshold based on the target
    # For example, stay if the current value is within 2 of the target
    threshold = target - 2

    # Decision logic
    if value >= threshold:
        return "STAY"
    else:
        return "HIT"
