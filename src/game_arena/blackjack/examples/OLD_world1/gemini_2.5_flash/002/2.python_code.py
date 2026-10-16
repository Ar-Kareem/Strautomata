
import random

def policy(hand: list[str], target: int) -> str:
    """
    Implements a policy for a simplified Blackjack-like game.

    Args:
        hand: A list of strings representing the cards currently held.
        target: The integer T to approach.

    Returns:
        "HIT" to draw another card, or "STAY" to stop drawing.
    """

    def calculate_hand_value(current_hand: list[str], current_target: int) -> int:
        """Calculates the current value of the hand, handling 'A' dynamically."""
        value = 0
        num_aces = 0
        for card in current_hand:
            if card.isdigit():
                value += int(card)
            elif card in ["J", "Q", "K"]:
                value += 10
            elif card == "A":
                num_aces += 1
                value += 11  # Initially assume Ace is 11

        # Adjust for Aces if busting or going over target with 11
        while value > current_target and num_aces > 0:
            value -= 10  # Change an Ace from 11 to 1
            num_aces -= 1
        return value

    current_value = calculate_hand_value(hand, target)

    # If we've already busted, it's too late. But the game engine should handle this.
    # Our policy should aim to prevent busting.
    if current_value > target:
        return "STAY"

    # Define a threshold for hitting
    # This is a basic strategy. We want to get close to the target without busting.
    # A common Blackjack strategy is to hit until 17 or higher.
    # Here, we adapt it to the target.

    # If our current hand is very low, we almost certainly want to hit.
    if current_value < target * 0.6: # Example: if target is 20, and we have less than 12
        return "HIT"

    # If we are very close to the target, it might be safer to STAY.
    # The risk of busting increases as we get closer.
    # This threshold can be tuned.
    if current_value >= target - 3: # If we are 0, 1, 2 away from target
        # Calculate the potential next card values (assuming ideal draw or knowing remaining deck)
        # For simplicity, let's just consider the average hit value.
        # Average value of cards (removing A for now as it's dynamic):
        # 2,3,4,5,6,7,8,9,10,10,10,10 (12 cards) -> sum = 94. Avg = 94/12 approx 7.8
        # If we include Ace as 1 (when it's safe) or 11 (when it's fine):
        # A, 2, ..., K -> approx (11+2+...+10+10+10+10)/13 = 101/13 ~ 7.7

        # Let's assess the risk of busting with different values and the number of remaining high cards.
        # This simple policy will just use a fixed threshold based on the current value.
        if current_value >= target - 1: # If current_value is T or T-1
            return "STAY"

        # If current_value is T-2 or T-3
        # We need to decide if hitting is worth the risk of going over.
        # A "safe" hit would be a card that doesn't push us over T.
        # If the difference is small, say 2 or 3, a 10-value card would bust us.
        # A "hard" stop helps prevent busts.
        if current_value >= target - 5: # If current_value is T-5, T-4, T-3, T-2
            # How many cards can we draw without busting?
            max_safe_hit = target - current_value
            # If max_safe_hit is small (e.g., 1, 2, 3, 4, 5)
            # The probability of drawing a higher card increases the risk.
            # Let's say if we need a 5 or less, we hit. But if we need 4 or less, we stay.
            # This is a heuristic.
            if max_safe_hit <= 4: # If we need a card of 4 or less to not bust
                # The chance of drawing a 5 or more (5,6,7,8,9,10,J,Q,K,A if Ace is 11) is high.
                # So, it's safer to STAY
                return "STAY"
            else:
                # If we can hit a 6 or more without busting, it's a good idea to hit.
                return "HIT"

    # Default strategy: If not too close to target and not too far, try to hit.
    return "HIT"

