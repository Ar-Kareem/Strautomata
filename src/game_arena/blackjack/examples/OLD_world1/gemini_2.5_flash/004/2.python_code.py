
import random

def get_card_value(card: str, current_hand_value: int, target: int) -> int:
    if card.isdigit():
        return int(card)
    elif card in ["J", "Q", "K"]:
        return 10
    elif card == "A":
        # "A" is 11 unless it makes the hand bust
        if current_hand_value + 11 <= target:
            return 11
        else:
            return 1
    return 0 # Should not happen

def calculate_hand_value(hand: list[str], target: int) -> int:
    value = 0
    num_aces = 0
    for card in hand:
        if card.isdigit():
            value += int(card)
        elif card in ["J", "Q", "K"]:
            value += 10
        elif card == "A":
            num_aces += 1
            value += 11 # Assume 11 initially

    # Adjust for Aces if busting or near bust
    while value > target and num_aces > 0:
        value -= 10 # Change an Ace from 11 to 1
        num_aces -= 1
    
    return value

def policy(hand: list[str], target: int) -> str:
    current_value = calculate_hand_value(hand, target)

    # Basic strategy: If current value is too high, stay to avoid busting.
    # The threshold for "too high" can be tuned.
    # A simple approach is to stay if further drawing is likely to bust.
    
    # If we already busted (this shouldn't happen based on game rules if called correctly,
    # but as a safety for calculation), then it's too late.
    if current_value > target:
        return "STAY"

    # If we are very close to the target, it might be safer to STAY.
    # The closeness threshold can be optimized.
    # For example, if we are within 2-3 points of the target, and drawing
    # a small card (2 or 3) still makes us susceptible to busting.
    
    # Consider what cards are left in our deck (not in hand)
    all_cards_in_deck = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    remaining_cards = [c for c in all_cards_in_deck if c not in hand]

    # Calculate the probability of busting if we HIT
    bust_count = 0
    if not remaining_cards: # Edge case: no cards left to draw
        return "STAY"

    for card_to_draw in remaining_cards:
        # Temporarily calculate value if we draw this card
        temp_value_if_hit = current_value
        
        # When checking for an Ace, we need to be careful with its dual value.
        # For this predictive step, we should assume the worst or best case.
        # If adding 11 busts, then it's 1. Otherwise, it's 11.
        if card_to_draw == "A":
            if current_value + 11 > target:
                temp_value_if_hit += 1
            else:
                temp_value_if_hit += 11
        else:
            temp_value_if_hit += get_card_value(card_to_draw, current_value, target) # Simplified A handling here

        if temp_value_if_hit > target:
            bust_count += 1
    
    bust_probability = bust_count / len(remaining_cards)

    # Threshold for busting. If we have a high chance of busting, STAY.
    # This threshold can be tuned. A common strategy in Blackjack is to hit
    # until a certain score is reached, or stay if the risk of bust is too high.
    
    # If the current value is already good and hitting has a high bust probability
    if current_value >= target - 3 and bust_probability > 0.5: # Example threshold
        return "STAY"
    
    # If the current value is far from the target and the bust probability is low, HIT.
    # This is a simple heuristic. More sophisticated policies would involve
    # Monte Carlo simulations or more advanced probability calculations.
    if current_value < target - 5 and bust_probability < 0.3: # Example threshold
        return "HIT"

    # Default strategy: If current value is relatively low and there's room to improve, HIT.
    # If current value is high and close to target, STAY.
    # The '16' or '17' rule in Blackjack is analogous here, but adjusted for 'target'.

    # If the current value is already close to the target, perhaps it's better to stay.
    # Consider the opponent: if the opponent is likely to bust, we might stay at a lower score.
    # However, we don't have opponent's info.

    # A simpler rule: continue hitting until we are "safe" or at high risk
    if current_value < target * 0.85: # arbitrary threshold, e.g., 85% of target
        return "HIT"

    # If we're getting closer to the target, consider the risk.
    # If we have a very good score (e.g., target-1 or target), definitely STAY.
    if current_value >= target - 1:
        return "STAY"

    # If the current value is such that any drawn card will likely bust, STAY.
    min_possible_draw = 1 # for an Ace that converts to 1
    if len(remaining_cards) > 0:
        min_possible_draw_val = min([get_card_value(c, current_value, target) for c in remaining_cards])
        if current_value + min_possible_draw_val > target:
            return "STAY"

    # If we are borderline, perhaps we should lean towards staying if the chance of busting is significant.
    if bust_probability > 0.4: # Another threshold
        return "STAY"

    # Otherwise, try to improve
    return "HIT"

