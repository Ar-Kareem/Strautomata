
import functools

def calculate_value(hand, target):
    total = 0
    aces = 0
    for card in hand:
        if card == 'A':
            total += 11
            aces += 1
        elif card in ('J', 'Q', 'K'):
            total += 10
        else:
            total += int(card)
    if total > target:
        total -= 10 * aces
    return total

# List of all cards in the deck
ALL_CARDS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']

# Memoized function to compute the best expected value for a given hand and target
@functools.lru_cache(maxsize=None)
def best_expected_value(hand_tuple, target):
    hand = list(hand_tuple)
    value = calculate_value(hand, target)
    
    if value > target:
        return -10000  # Represents a busted hand
    
    remaining_cards = [card for card in ALL_CARDS if card not in hand]
    
    if not remaining_cards:
        return value
    
    hit_values = []
    for card in remaining_cards:
        new_hand = hand + [card]
        new_hand_tuple = tuple(sorted(new_hand))
        hit_values.append(best_expected_value(new_hand_tuple, target))
    
    hit_avg = sum(hit_values) / len(remaining_cards)
    return max(value, hit_avg)

def policy(hand: list[str], target: int) -> str:
    hand_tuple = tuple(sorted(hand))
    value = calculate_value(hand, target)
    remaining_cards = [card for card in ALL_CARDS if card not in hand]

    if not remaining_cards:
        return "STAY"
    
    hit_values = []
    for card in remaining_cards:
        new_hand = hand + [card]
        new_hand_tuple = tuple(sorted(new_hand))
        hit_values.append(best_expected_value(new_hand_tuple, target))
    
    hit_avg = sum(hit_values) / len(remaining_cards)

    return "HIT" if hit_avg > value else "STAY"
