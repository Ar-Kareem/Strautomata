
import numpy as np
from functools import lru_cache

def calculate_hand_value(hand: list[str], target: int) -> int:
    """Calculate the current hand value considering Aces as 11 or 1."""
    value = 0
    aces = 0
    for card in hand:
        if card == "A":
            aces += 1
            value += 11
        elif card in ["J", "Q", "K"]:
            value += 10
        else:
            value += int(card)

    # Adjust for Aces if hand value exceeds target
    while value > target and aces > 0:
        value -= 10
        aces -= 1
    return value

def get_possible_next_hands(hand: list[str], deck: list[str]) -> list[list[str]]:
    """Generate all possible next hands by drawing one card from the remaining deck."""
    remaining_deck = [card for card in deck if card not in hand]
    next_hands = []
    for card in remaining_deck:
        next_hands.append(hand + [card])
    return next_hands

def simulate_game(hand: list[str], target: int, deck: list[str]) -> float:
    """Simulate the game to estimate the probability of winning."""
    current_value = calculate_hand_value(hand, target)
    if current_value > target:
        return 0.0  # Already busted

    # If we're already at or over the target, stay
    if current_value >= target:
        return 1.0

    # If we have no cards left to draw, stay
    if len(deck) == 0:
        return 1.0

    # Get all possible next hands
    next_hands = get_possible_next_hands(hand, deck)

    # Simulate each possible next hand
    win_probabilities = []
    for next_hand in next_hands:
        next_value = calculate_hand_value(next_hand, target)
        if next_value > target:
            win_probabilities.append(0.0)
        else:
            # If we stay, we win if the opponent busts or if our value is closer to target
            # For simplicity, assume opponent has a 50% chance of busting if they have >= 2 cards
            # and a 20% chance if they have 1 card (simplified heuristic)
            opponent_bust_chance = 0.5 if len(next_hand) >= 2 else 0.2
            win_prob = opponent_bust_chance + (1 - opponent_bust_chance) * 0.5  # 50% chance of being closer
            win_probabilities.append(win_prob)

    # If all next hands lead to bust, stay
    if all(p == 0.0 for p in win_probabilities):
        return 0.0

    # If all next hands lead to win, hit
    if all(p > 0.0 for p in win_probabilities):
        return 1.0

    # Otherwise, choose the action with the highest average win probability
    avg_win_prob_hit = np.mean(win_probabilities)
    avg_win_prob_stay = 0.5  # Base chance of winning if we stay (simplified)

    return avg_win_prob_hit if avg_win_prob_hit > avg_win_prob_stay else 1.0

def policy(hand: list[str], target: int) -> str:
    """Determine whether to HIT or STAY based on the current hand and target."""
    # Full deck is all 13 cards
    full_deck = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    remaining_deck = [card for card in full_deck if card not in hand]

    current_value = calculate_hand_value(hand, target)

    # If we're already busted, return STAY (though this shouldn't happen in policy)
    if current_value > target:
        return "STAY"

    # If we're at or over the target, stay
    if current_value >= target:
        return "STAY"

    # If we have no cards left to draw, stay
    if len(remaining_deck) == 0:
        return "STAY"

    # Heuristic rules
    # If we have a high value hand, stay
    if current_value >= target - 5:
        return "STAY"

    # If we have a low value hand and few cards, hit
    if current_value < 10 and len(hand) < 3:
        return "HIT"

    # If we have an Ace and a low value, hit
    if "A" in hand and current_value < 12:
        return "HIT"

    # If we have a high chance of busting, stay
    if current_value + 10 > target and len(hand) >= 2:
        return "STAY"

    # Simulate the game to decide
    win_prob_hit = simulate_game(hand, target, remaining_deck)
    win_prob_stay = 0.5  # Base chance of winning if we stay

    if win_prob_hit > win_prob_stay:
        return "HIT"
    else:
        return "STAY"
