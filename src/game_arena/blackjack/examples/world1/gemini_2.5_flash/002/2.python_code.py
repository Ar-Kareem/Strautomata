
import collections

def calculate_hand_value(hand: list[str], target: int) -> int:
    """
    Calculates the value of a hand according to the game rules,
    handling Aces dynamically based on the target.

    Args:
        hand: The list of strings representing the cards in the hand.
        target: The integer T for which Ace values are adjusted (11 if <= T, else 1).

    Returns:
        The total value of the hand.
    """
    current_sum = 0
    num_aces = 0
    card_values = {
        "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10,
        "J": 10, "Q": 10, "K": 10
    }

    # First, sum all non-Ace cards and count Aces.
    # Assume Aces are 11 initially.
    for card in hand:
        if card == "A":
            num_aces += 1
            current_sum += 11  # Optimistically treat Ace as 11
        else:
            current_sum += card_values[card]

    # Adjust Aces if the total value exceeds the target.
    # An Ace counted as 11 can be converted to 1 if doing so prevents busting
    # or keeps the hand value <= target.
    while current_sum > target and num_aces > 0:
        current_sum -= 10  # Convert an 11-value Ace to a 1-value Ace
        num_aces -= 1

    return current_sum

def policy(hand: list[str], target: int) -> str:
    """
    Implements a policy for a simplified Blackjack-like game.

    The policy aims to get as close to the target score as possible without busting.
    It uses a fixed threshold relative to the target to decide whether to HIT or STAY.

    Args:
        hand: The list of strings representing the cards you currently hold.
        target: The integer T you are trying to approach.

    Returns:
        One of the two actions as a string: "HIT" or "STAY".
    """
    current_score = calculate_hand_value(hand, target)

    # Rule: If at any point the sum of your card values is greater than target, you bust and immediately lose.
    # This implies that `policy` will never be called when `current_score > target`.
    # Therefore, we only need to consider `current_score <= target`.

    # If the current score is exactly the target, there's no way to improve, so STAY.
    if current_score == target:
        return "STAY"
    
    # Policy threshold:
    # The goal is to maximize the score without busting.
    # If the current score is far from the target, hitting is generally safe.
    # If the current score is close to the target, hitting carries a high risk of busting.
    #
    # A common strategy in blackjack-like games is to stand when the score is 17 or higher
    # in a standard game where 21 is target. This is equivalent to `target - 4`.
    # Let's apply a similar relative threshold here: `target - 4`.

    # If current_score is less than (target - 4), it means there's enough room
    # to draw a high-value card (e.g., 10) without immediately busting.
    # Example: target=20. If score=15 (15 < 20-4 is False), STAY.
    # Example: target=20. If score=14 (14 < 20-4 is True), HIT.
    # This means we hit on scores up to `target - 5`.
    # We stay on scores from `target - 4` all the way up to `target`.

    # Let's analyze the threshold `target - 4`:
    # If `current_score = target - 4` (e.g., target=20, score=16):
    #   - Drawing an Ace (1): new_score = 17 (safe, good)
    #   - Drawing a 2: new_score = 18 (safe, good)
    #   - Drawing a 3: new_score = 19 (safe, good)
    #   - Drawing a 4: new_score = 20 (perfect!)
    #   - Drawing a 5 or higher: new_score > 20 (BUST)
    # Cards 5, 6, 7, 8, 9, 10, J, Q, K are 9 cards out of 13 that would cause a bust.
    # This indicates a very high risk (approx 69% chance of busting if all cards are available).
    # Therefore, it is prudent to STAY if `current_score >= target - 4`.

    if current_score < target - 4:
        # It's relatively safe to hit.
        return "HIT"
    else:
        # The score is close to the target; hitting carries a high risk of busting.
        # It's safer to stay.
        return "STAY"

