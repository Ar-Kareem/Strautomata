
def card_value(card: str) -> int:
    if card.isdigit():
        return int(card)
    elif card in ("J", "Q", "K"):
        return 10
    elif card == "A":
        return 11
    else:
        raise ValueError(f"Invalid card: {card}")


def hand_value(hand: list[str], target: int) -> int:
    ace_count = hand.count("A")
    total = 0
    for card in hand:
        total += card_value(card)

    while total > target and ace_count > 0:
        total -= 10
        ace_count -= 1

    return total


def policy(hand: list[str], target: int) -> str:
    hand_value_current = hand_value(hand, target)
    if hand_value_current > target:
        return "STAY"

    # Simple strategy: stay if close to target.
    threshold = target - 4
    if hand_value_current >= threshold:
        return "STAY"
    else:
        return "HIT"
