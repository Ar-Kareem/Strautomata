
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

    # Adjust for aces if the value exceeds the target
    while value > target and aces > 0:
        value -= 10
        aces -= 1

    # Decision making
    if value >= target:
        return "STAY"
    else:
        # Calculate the minimum and maximum possible values of the next card
        min_next = 1  # minimum value of the next card (Ace as 1)
        max_next = 10  # maximum value of the next card (10, J, Q, K)

        # If the current value plus the minimum next card is greater than or equal to the target, stay
        if value + min_next >= target:
            return "STAY"
        # If the current value plus the maximum next card is less than the target, hit
        elif value + max_next < target:
            return "HIT"
        else:
            # If there's a risk of busting, decide based on a threshold
            # For example, stay if the current value is within 4 of the target
            if value >= target - 4:
                return "STAY"
            else:
                return "HIT"
