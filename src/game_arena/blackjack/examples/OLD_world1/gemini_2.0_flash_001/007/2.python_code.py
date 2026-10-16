
def policy(hand: list[str], target: int) -> str:
    """
    Determines whether to HIT or STAY based on the current hand and target score.

    Args:
        hand: A list of strings representing the cards in the current hand.
        target: The target score for the game.

    Returns:
        "HIT" or "STAY" as a string.
    """

    def calculate_hand_value(hand: list[str], target: int) -> int:
        """
        Calculates the value of a hand, treating Aces as 11 or 1.
        """
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
        return "STAY"  # Already busted, but the game might require a move

    if hand_value == target :
        return "STAY"

    # Implement a simple strategy:
    # HIT if the hand value is less than 17, otherwise STAY.
    if hand_value < 17:
        return "HIT"
    else:
        return "STAY"
