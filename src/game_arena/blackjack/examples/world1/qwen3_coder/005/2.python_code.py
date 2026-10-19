
import math

# Full deck of 13 cards
FULL_DECK = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

# Card value mapping
CARD_VALUES = {
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6,
    "7": 7, "8": 8, "9": 9, "10": 10,
    "J": 10, "Q": 10, "K": 10
}
# Ace is handled separately as 1 or 11


def calculate_hand_value(hand: list[str], target: int) -> int:
    """Calculate the best possible value of the hand without exceeding target."""
    # First, sum all cards assuming ace is 1
    value = 0
    ace_count = 0
    for card in hand:
        if card == "A":
            ace_count += 1
            value += 1
        else:
            value += CARD_VALUES[card]
    
    # Try to promote aces from 1 to 11 as long as we don't bust
    for _ in range(ace_count):
        if value + 10 <= target:
            value += 10
        else:
            break

    return value


def policy(hand: list[str], target: int) -> str:
    current_value = calculate_hand_value(hand, target)

    # If already at or above target, no reason to hit
    if current_value >= target:
        return "STAY"

    # Determine remaining cards in the deck
    # We assume we draw from our own full 13-card deck in order
    # So we need to find out which cards we still have left to draw
    # This is not explicitly given, but we know we start with full deck
    # So let's assume that hand is always a subset and we draw in order?
    # Wait— the problem says "you draw the next card from your deck"
    # but it does not specify an initial order or draw mechanism.
    # A safe assumption is that we start with a shuffled deck, and you draw from the remaining unseen cards.
    # But we're given only `hand` and not draw order or seen cards.
    # So a reasonable interpretation is that we have a full deck, and we can draw from the remaining cards
    # that are NOT in `hand`.

    # Count occurrences in hand to determine remaining cards
    hand_counts = {}
    for card in hand:
        hand_counts[card] = hand_counts.get(card, 0) + 1

    # All cards are unique in a single suit deck, so max 1 of each
    # So remaining cards are those not in hand
    remaining_deck = []
    for card in FULL_DECK:
        if hand_counts.get(card, 0) == 0:
            remaining_deck.append(card)

    # If no cards left, must stay
    if not remaining_deck:
        return "STAY"

    # Simulate each possible next card draw
    bust_count = 0
    total_outcomes = len(remaining_deck)
    new_values = []

    for card in remaining_deck:
        new_hand = hand + [card]
        new_value = calculate_hand_value(new_hand, target)
        if new_value > target:
            bust_count += 1
        else:
            new_values.append(new_value)

    # If all outcomes bust
    if bust_count == total_outcomes:
        return "STAY"

    bust_probability = bust_count / total_outcomes
    expected_gain = 0.0
    if new_values:
        expected_new_value = sum(new_values) / len(new_values)
        expected_gain = expected_new_value - current_value

    # Decision criteria
    # If we're already pretty close, be more conservative
    margin = target - current_value

    # Heuristic thresholds
    # If bust chance is high, STAY
    if bust_probability > 0.4:
        return "STAY"

    # If margin is small, STAY unless gain is significant
    if margin <= 2:
        if bust_probability <= 0.2 and expected_gain > 0.1:
            return "HIT"
        else:
            return "STAY"

    # If margin is medium, HIT if moderate chance of gain
    if 3 <= margin <= 5:
        if bust_probability <= 0.3 and expected_gain > 0.2:
            return "HIT"
        else:
            return "STAY"

    # If margin is large, be more aggressive
    if margin > 5:
        if bust_probability <= 0.5:  # Even at 50%, if we're far, it's worth the risk
            return "HIT"
        else:
            return "STAY"

    # Default to STAY if uncertain
    return "STAY"
