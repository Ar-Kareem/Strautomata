
import random

def policy(hand: list[str], target: int) -> str:
    """
    Implements a policy for a simplified Blackjack-like game.

    Args:
        hand: The list of strings representing the cards you currently hold.
        target: The integer T you are trying to approach.

    Returns:
        One of the two actions as a string: "HIT" or "STAY".
    """

    def calculate_hand_value(current_hand: list[str], current_target: int) -> tuple[int, bool]:
        """
        Calculates the value of the hand, handling Ace's flexible value.
        Returns the total value and a boolean indicating if an Ace was counted as 11.
        """
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

        # Adjust Ace value if hand busts or goes over target
        while value > current_target and num_aces > 0:
            value -= 10  # Change an Ace from 11 to 1
            num_aces -= 1
        
        return value, num_aces > 0 # Return if an Ace was used as 11

    current_value, _ = calculate_hand_value(hand, target)

    # If already busted, something went wrong or strategy needs rethinking, but for now, stay.
    if current_value > target:
        return "STAY"

    # Define a threshold for hitting
    # This threshold is a balance between getting closer to the target and busting
    # Let's try a dynamic threshold based on the target.
    # If the target is high, we can afford to take more risks.
    # If the target is low, we need to be more conservative.

    # A simple heuristic:
    # If current value is far from target, and we have a low chance of busting with a HIT
    # then HIT.
    # The chance of busting depends on the remaining cards in the deck, but we don't know that.
    # So we'll use a fixed risk assessment.

    # The aggressive hitting strategy continues as long as the current hand value
    # is significantly less than the target.
    # We need to estimate the potential impact of a "HIT".
    # The average card value is roughly (2+10*4+11)/13 approx 6-7.
    
    # If the current value is very low, we almost always want to hit.
    if current_value < target - 6:  # This gives us room for a high card
        return "HIT"

    # If the current value is close to the target, we need to be more careful.
    # Consider what would happen if we draw a high card (e.g., 10).
    # If current_value + 10 would bust us, we should consider staying.
    if current_value + 10 > target:
        # If adding a high card makes us bust, we should probably stay,
        # unless our current value is so low that staying guarantees a loss.
        # But this is a simplified opponent, we don't know their hand.
        # So, we prioritize not busting ourselves.
        return "STAY"
    
    # If we are in the middle ground, we can be slightly more aggressive if the target is high.
    # For example, if target is 25, and current is 18. Hit is reasonable.
    # If target is 15, and current is 10. Hit is reasonable.
    # Let's use a threshold that makes us more likely to hit for higher targets.
    
    # Example thresholds:
    # If target is 20, hit until 16-17, then stay.
    # If target is 15, hit until 11-12, then stay.
    # This suggests (target - X) where X is 3-4.

    # Let's use a simple static threshold relative to the target for now.
    # This value represents the maximum score difference before we consider staying.
    # A smaller diff_threshold means we are more conservative.
    diff_threshold = 3 

    if target - current_value <= diff_threshold:
        return "STAY"
    else:
        return "HIT"

