
import random
from collections import defaultdict

def policy(hand: list[str], target: int) -> str:
    # Precompute card values
    def card_value(card):
        if card == 'A':
            return 11 if sum_values(hand) <= target else 1
        elif card in ['J', 'Q', 'K']:
            return 10
        else:
            return int(card)

    def sum_values(cards):
        return sum(card_value(card) for card in cards)

    current_sum = sum_values(hand)

    # If we're already over, we've already busted (but this shouldn't happen in policy)
    if current_sum > target:
        return "STAY"

    # If we're exactly at target, stay
    if current_sum == target:
        return "STAY"

    # If we're very close to target, stay
    if current_sum >= target - 2:
        return "STAY"

    # If we have only one card left in our deck and we're not close, stay
    if len(hand) == 12 and current_sum < target - 5:
        return "STAY"

    # If we have an Ace that could be 1, and we're close to busting, stay
    if 'A' in hand and current_sum + 1 > target:
        return "STAY"

    # If we're far from target and have many cards left, hit
    if current_sum < target - 8 and len(hand) > 5:
        return "HIT"

    # If we have a good chance of reaching target with one more card
    if current_sum < target - 3 and len(hand) > 6:
        return "HIT"

    # If we have a high probability of busting with one more card
    if current_sum > target - 5 and len(hand) > 7:
        return "STAY"

    # Monte Carlo simulation to estimate best move
    if random.random() < 0.3:  # 30% chance to use simulation
        remaining_cards = [c for c in ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
                          if c not in hand]
        random.shuffle(remaining_cards)

        # Try hitting once
        if remaining_cards:
            next_card = remaining_cards[0]
            new_sum = current_sum + card_value(next_card)
            if new_sum <= target:
                return "HIT"

        # Try hitting twice
        if len(remaining_cards) >= 2:
            new_sum = current_sum
            for card in remaining_cards[:2]:
                new_sum += card_value(card)
                if new_sum > target:
                    break
            if new_sum <= target:
                return "HIT"

    # Default strategy: hit if we're not close to target
    return "HIT" if current_sum < target - 4 else "STAY"
