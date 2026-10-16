
import random

def get_card_value(card: str, current_total: int, target: int) -> int:
    if card.isdigit():
        return int(card)
    elif card in ["J", "Q", "K"]:
        return 10
    elif card == "A":
        # "A" is 11 if current_total + 11 <= target, otherwise 1
        if current_total + 11 <= target:
            return 11
        else:
            return 1
    return 0 # Should not happen

def calculate_hand_value(hand: list[str], target: int) -> int:
    # First pass, calculate without considering 'A' as 1
    # This approach prioritizes 'A' as 11 if possible
    temp_sum = 0
    num_aces = 0
    for card in hand:
        if card == "A":
            num_aces += 1
            temp_sum += 11  # Assume 'A' is 11 initially
        elif card.isdigit():
            temp_sum += int(card)
        else: # J, Q, K
            temp_sum += 10

    # Adjust for aces if bust or over target
    while temp_sum > target and num_aces > 0:
        temp_sum -= 10  # Change an 'A' from 11 to 1
        num_aces -= 1
    
    return temp_sum

def policy(hand: list[str], target: int) -> str:
    current_value = calculate_hand_value(hand, target)

    # If already busted, no point in hitting (though this state might not be reachable through policy)
    if current_value > target:
        return "STAY"

    # If close to target, stay
    if current_value >= target - 2:  # Or some other threshold like target - 3
        return "STAY"

    # Consider the risk of hitting based on possible next cards
    # We don't know the opponent's hand or their deck, so we focus on our own risk.

    # Estimate the average value of remaining cards (simple heuristic)
    # This assumes we have a full deck initially and cards are removed from it.
    # However, the problem statement says "You have your own 13-card deck (one copy of each rank)"
    # This implies that the deck is fixed and we draw from it. We don't know what's left.
    # For a deterministic policy, we just need to decide based on current hand and target.

    # A simple strategy:
    # If our current value is significantly lower than the target, hit.
    # The threshold for "significantly lower" needs to be determined.
    # We want to get as close to the target as possible without busting.

    # If our current value is too low to likely win, we must hit.
    # Example: If target is 20 and we have 5, we almost certainly need to hit.
    
    # We need to make sure we don't bust.
    # What's the probability of busting if we hit?
    # This is hard to calculate without knowing remaining cards.
    # A safer approach is to hit until a certain threshold is reached.

    # Let's define a "safe" hitting range.
    # If current_value + max_possible_card_value (11 for Ace, or 10 for face cards/10) is <= target
    # this doesn't fully capture "safe" because the max_possible_card_value could be an ace that turns into 1
    # For now, a simpler threshold strategy:

    # If we are very close to the target, STAY.
    # The exact threshold depends on how risky we want to be.
    # If the opponent plays optimally, they will try to reach target or slightly below.

    # Let's consider a threshold where we decide to stay.
    # This threshold should be high enough to be competitive but low enough to avoid busting frequently.
    
    # If the current value is already very high (e.g., within 2-3 of the target), it's generally safer to STAIY.
    if target - current_value <= 2: # If we are 0, 1, or 2 away from target
        return "STAY"
    
    # If hitting with a guaranteed non-bust card (e.g., if we can't draw anything >= (target - current_value + 1))
    # This is complex without deck knowledge.

    # A more robust simple strategy:
    # Hit if the current total is low.
    # Stay if the current total is high (close to target).

    # Example thresholds:
    # If current_value is <= target - 5, it's generally safe to hit.
    # If current_value is > target - 5, then consider carefully.
    
    # Let's define a risk tolerance.
    # If current_value + some_average_card_value <= target, then hit.
    # Average card value is around (2+3+...+10+10+10+10+11)/13 = (75+11)/13 = 86/13 approx 6.6
    
    # If we hit, what's a reasonable expectation?
    # If current_value + 11 (max possible hit from A) is <= target, then we are very safe.
    # If current_value + 10 (max possible hit from 10/J/Q/K) is <= target, still very safe.

    # This simple strategy aims to reach as close to target without busting.

    # Aggressive strategy: Keep hitting until very close to target (e.g., 1-2 points away).
    # Conservative strategy: Stay earlier to minimize bust risk.

    # Let's try an aggressive strategy: hit unless we are within 2 or 1 of the target.
    # This means staying at total = target, target-1, target-2.
    if current_value >= target - 2:
        return "STAY"
    else:
        return "HIT"

