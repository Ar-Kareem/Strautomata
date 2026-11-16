
def policy(hand: list[str], target: int) -> str:
    """
    A policy for a simplified Blackjack-like game.

    Args:
        hand: The list of strings representing the cards you currently hold.
        target: The integer target you are trying to approach.

    Returns:
        "HIT" — you draw the next card from your deck.
        "STAY" — you stop drawing cards for the rest of the game.
    """

    def calculate_hand_value(hand: list[str], target: int) -> int:
        """Calculates the value of a hand."""
        ace_count = hand.count("A")
        total = 0
        for card in hand:
            if card.isdigit():
                total += int(card)
            elif card in ("J", "Q", "K"):
                total += 10
            elif card == "A":
                total += 11
        while total > target and ace_count > 0:
            total -= 10
            ace_count -= 1
        return total

    hand_value = calculate_hand_value(hand, target)

    if hand_value > target:
        return "STAY"  # Already busted, no point in hitting

    # Basic strategy: hit if below 17, stay otherwise (adjust based on target)
    if target >= 25:
        hit_threshold = target - 8
    elif target >= 20:
        hit_threshold = target - 7
    else:
        hit_threshold = target - 6


    if hand_value < hit_threshold:
        return "HIT"
    else:
        return "STAY"
