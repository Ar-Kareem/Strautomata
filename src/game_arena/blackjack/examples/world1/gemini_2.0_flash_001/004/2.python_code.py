
def policy(hand: list[str], target: int) -> str:
    """
    Determines whether to HIT or STAY in a simplified Blackjack game.

    Args:
        hand: A list of strings representing the cards in the player's hand.
        target: The target score to reach.

    Returns:
        "HIT" if the player should draw another card, "STAY" otherwise.
    """

    def calculate_hand_value(hand: list[str]) -> int:
        """Calculates the value of a hand."""
        ace_count = 0
        total = 0
        for card in hand:
            if card.isdigit():
                total += int(card)
            elif card in ("J", "Q", "K"):
                total += 10
            elif card == "A":
                ace_count += 1

        for _ in range(ace_count):
            if total + 11 <= target:
                total += 11
            else:
                total += 1

        return total

    hand_value = calculate_hand_value(hand)

    if hand_value > target:
        return "STAY"  # Should not happen

    threshold = target - 4
    if hand_value < threshold:
        return "HIT"
    else:
        return "STAY"
