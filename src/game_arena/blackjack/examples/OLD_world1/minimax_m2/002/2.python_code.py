
def calculate_hand_value(hand, target):
    """
    Calculate the hand value with Ace adjustment based on the target score.
    Aces are valued as 11 if the hand value would be <= target after including the Ace as 11,
    otherwise as 1. This adjustment is applied by reducing 10 per Ace until the hand value <= target.
    """
    value = 0
    ace_count = 0
    for card in hand:
        if card == "A":
            value += 11
            ace_count += 1
        elif card in ["J", "Q", "K"]:
            value += 10
        else:
            value += int(card)  # For "2" to "10"
    # Adjust Aces to reduce the hand value to <= target
    while value > target and ace_count > 0:
        value -= 10
        ace_count -= 1
    return value

def policy(hand, target):
    """
    Decide whether to HIT or STAY based on the current hand and target score.
    Strategy: HIT if hand value is less than target minus 6, otherwise STAY.
    This threshold is based on the average card value (approximately 6.6) and is chosen to balance
    the risk of busting with the need to get close to the target.
    """
    hand_value = calculate_hand_value(hand, target)
    if hand_value < target - 6:
        return "HIT"
    else:
        return "STAY"
