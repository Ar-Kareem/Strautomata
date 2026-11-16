
import random

# Define the full deck of 13 distinct cards
FULL_DECK = set(['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K'])

def hand_value(hand, target):
    """
    Compute the hand value for a given hand and target.
    The Ace is counted as 11 initially, and if the total exceeds the target, 
    we reduce by 10 for each Ace until the total is <= target or all Aces are reduced.
    """
    total = 0
    num_aces = 0
    for card in hand:
        if card == 'A':
            total += 11
            num_aces += 1
        elif card in ['J', 'Q', 'K']:
            total += 10
        else:
            total += int(card)
    
    # Reduce by 10 for each Ace until the total <= target or no Aces left to reduce
    while total > target and num_aces > 0:
        total -= 10
        num_aces -= 1
    return total

def policy(hand, target):
    # If there are no cards left in the deck, we must stay.
    remaining_deck = FULL_DECK - set(hand)
    if not remaining_deck:
        return "STAY"
    
    current_value = hand_value(hand, target)
    
    # If we have busted (current_value > target), we lose, so we return STAY to end the game.
    # However, the policy should not be called in a busted state in a well-implemented game.
    if current_value > target:
        return "STAY"
    
    # Use threshold: if current_value >= target - 5, we stay; otherwise, we hit.
    threshold = target - 5
    if current_value >= threshold:
        return "STAY"
    else:
        return "HIT"
