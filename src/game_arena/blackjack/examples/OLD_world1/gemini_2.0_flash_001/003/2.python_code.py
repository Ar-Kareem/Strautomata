
import random

def card_value(card: str, current_sum: int, target: int) -> int:
    """Returns the value of a card."""
    if card.isdigit():
        return int(card)
    elif card in ("J", "Q", "K"):
        return 10
    else:  # card == "A"
        if current_sum + 11 <= target:
            return 11
        else:
            return 1

def hand_value(hand: list[str], target: int) -> int:
    """Calculates the value of a hand."""
    sum_val = 0
    for card in hand:
        sum_val += card_value(card, sum_val, target)
    return sum_val

def policy(hand: list[str], target: int) -> str:
    """
    Determines whether to hit or stay based on the current hand and target score.
    """
    current_sum = hand_value(hand, target)

    if current_sum > target:
        return "STAY"  # Already busted, so stay to avoid further penalty

    # Basic strategy: hit if below a certain threshold, stay otherwise

    if current_sum <= target // 2: # Aggressive early play
        return "HIT"

    if current_sum < target - 4: # Hit if far away to potentially catch up later
      return "HIT"

    if current_sum < target: # Hit if you are below target
         # Adjust probabilities dynamically based on your proximity to target and opponent's potential score
           if random.random() < 0.6: # Reduced probability of hitting as approach target
              return "HIT"
           else:
              return "STAY"
    
    # If all above conditions are false, choose stay to not bust.
    return "STAY"
