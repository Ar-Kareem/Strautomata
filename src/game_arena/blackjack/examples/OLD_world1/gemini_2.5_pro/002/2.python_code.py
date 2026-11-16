
import math

# This module defines the policy for a simplified Blackjack-like game.
# The policy function decides whether to "HIT" or "STAY" based on the
# player's hand and the game's target score.

# A dictionary to map card strings to their primary numerical values.
# The 'A' (Ace) is handled separately as its value depends on the context.
CARD_VALUES = {
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10,
    "J": 10, "Q": 10, "K": 10
}

def _calculate_hand_value(hand: list[str], target: int) -> tuple[int, int]:
    """
    Calculates the value of a hand, accounting for the flexible value of Aces.

    The Ace rule is:
    - An 'A' is counted as 11 if the total hand value is <= target.
    - An 'A' is counted as 1 if the total hand value would otherwise be > target.

    Args:
        hand: A list of card strings representing the hand.
        target: The target score for the current game.

    Returns:
        A tuple containing:
        - The calculated score of the hand.
        - The number of aces currently being counted as 11 (indicating a "soft" hand).
    """
    value = 0
    num_aces = 0

    for card in hand:
        if card == "A":
            num_aces += 1
        else:
            value += CARD_VALUES[card]

    # Add aces, initially counting each as 11.
    value += num_aces * 11
    soft_aces_used = num_aces

    # If the value exceeds the target, convert aces from 11 to 1 one by one
    # until the value is no longer over the target or no soft aces are left.
    while value > target and soft_aces_used > 0:
        value -= 10  # Change an Ace's value from 11 to 1.
        soft_aces_used -= 1

    return value, soft_aces_used


def policy(hand: list[str], target: int) -> str:
    """
    Implements a policy for a simplified Blackjack-like game.

    The policy is based on a threshold strategy derived from standard Blackjack
    "basic strategy", scaled to the game's target score `T`.

    Args:
        hand: A list of strings representing the cards currently held.
        target: The target score for the game.

    Returns:
        A string, either "HIT" or "STAY".
    """
    # On the first turn with an empty hand, always draw a card.
    if not hand:
        return "HIT"

    # Calculate the current value of the hand and check for soft aces.
    current_value, num_soft_aces = _calculate_hand_value(hand, target)

    # If we've hit the target exactly, there is no way to improve the score,
    # so we should always stay.
    if current_value == target:
        return "STAY"

    # --- Strategy Core: Scaled Blackjack Heuristic ---
    # The core of the strategy is to establish a "stop score." If the current
    # hand value is at or above this score, we STAY; otherwise, we HIT.

    # These stop scores are determined by scaling the well-known Blackjack
    # basic strategy for a target of 21. In standard Blackjack, a solid baseline
    # is to STAY on a "hard" 17 and "soft" 19. We use these as ratios
    # (17/21 and 19/21) to find equivalent stop scores for any given target `T`.
    # This provides a robust and adaptable strategy, as it's based on a
    # time-tested heuristic that balances risk and reward. In a symmetric game
    # where the opponent's strategy is unknown, adopting a solid, standard
    # strategy is a reliable approach.

    # Stop score for "hard" hands (no ace counted as 11).
    hard_stop_factor = 17 / 21
    hard_stop_score = math.floor(target * hard_stop_factor)

    # Stop score for "soft" hands (at least one ace counted as 11).
    soft_stop_factor = 19 / 21
    soft_stop_score = math.floor(target * soft_stop_factor)

    # --- Decision Logic ---
    if num_soft_aces > 0:
        # For "soft" hands, we can be more aggressive. Drawing a high card
        # is less risky, as the ace's value can be reduced from 11 to 1 to
        # avoid a bust.
        if current_value >= soft_stop_score:
            return "STAY"
        else:
            return "HIT"
    else:
        # For "hard" hands, the risk of busting is higher, so we are
        # more conservative.
        if current_value >= hard_stop_score:
            return "STAY"
        else:
            return "HIT"
