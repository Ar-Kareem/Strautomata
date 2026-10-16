
import random
from collections import Counter

def calculate_hand_value(hand, target):
    value = 0
    aces = 0
    for card in hand:
        if card in ['J', 'Q', 'K']:
            value += 10
        elif card == 'A':
            value += 11
            aces += 1
        else:
            value += int(card)

    while value > target and aces > 0:
        value -= 10
        aces -= 1

    return value

def policy(hand, target):
    current_value = calculate_hand_value(hand, target)

    # If we're already at or above the target, stay
    if current_value >= target:
        return "STAY"

    # If we're very close to the target, stay to avoid busting
    if target - current_value <= 2:
        return "STAY"

    # If we're far from the target, hit to try to improve
    if target - current_value > 5:
        return "HIT"

    # Calculate the probability of improving vs busting
    remaining_cards = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
    hand_counter = Counter(hand)
    for card in hand_counter:
        remaining_cards = [c for c in remaining_cards if c != card or hand_counter[card] < 1]

    improve_count = 0
    bust_count = 0

    for card in remaining_cards:
        new_hand = hand + [card]
        new_value = calculate_hand_value(new_hand, target)
        if new_value > target:
            bust_count += 1
        elif new_value > current_value:
            improve_count += 1

    # If the probability of improving is higher than busting, hit
    if improve_count > bust_count:
        return "HIT"
    else:
        return "STAY"
