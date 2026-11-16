
import functools

ALL_CARDS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

def calculate_value(hand, target):
    total = 0
    aces = 0
    for card in hand:
        if card in ['J', 'Q', 'K']:
            total += 10
        elif card == 'A':
            total += 11
            aces += 1
        else:
            total += int(card)
    if total <= target:
        return total
    for _ in range(aces):
        total -= 10
        if total <= target:
            return total
    return -1

@functools.lru_cache(maxsize=None)
def best_value(hand_tuple, target):
    hand = list(hand_tuple)
    current_value = calculate_value(hand, target)
    if current_value == -1:
        return -1
    remaining_cards = [card for card in ALL_CARDS if card not in hand]
    if not remaining_cards:
        return current_value
    total_hit_value = 0.0
    for card in remaining_cards:
        new_hand = hand + [card]
        new_hand_sorted = tuple(sorted(new_hand))
        new_best = best_value(new_hand_sorted, target)
        total_hit_value += new_best
    average_hit_value = total_hit_value / len(remaining_cards)
    return max(current_value, average_hit_value)

def policy(hand: list[str], target: int) -> str:
    sorted_hand = tuple(sorted(hand))
    current_value_hand = calculate_value(hand, target)
    if current_value_hand == -1:
        return "STAY"
    remaining_cards = [card for card in ALL_CARDS if card not in hand]
    if not remaining_cards:
        return "STAY"
    total_hit_value = 0.0
    for card in remaining_cards:
        new_hand = hand + [card]
        new_hand_sorted = tuple(sorted(new_hand))
        new_best = best_value(new_hand_sorted, target)
        total_hit_value += new_best
    average_hit_value = total_hit_value / len(remaining_cards)
    if average_hit_value > current_value_hand:
        return "HIT"
    else:
        return "STAY"
