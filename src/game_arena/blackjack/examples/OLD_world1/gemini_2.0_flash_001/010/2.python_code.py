
def policy(hand: list[str], target: int) -> str:
    """
    A policy for a simplified Blackjack-like game.

    Args:
        hand: The list of strings representing the cards you currently hold.
        target: The integer T you are trying to approach.

    Returns:
        "HIT" if you should draw the next card from your deck, or "STAY" if you should stop drawing cards.
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
        return "STAY"

    # Simple policy: HIT if hand value is below a threshold, otherwise STAY
    if hand_value < target - 2:
        return "HIT"
    else:
        return "STAY"
