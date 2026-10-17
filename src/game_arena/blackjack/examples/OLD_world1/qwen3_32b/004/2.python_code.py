
import functools

ALL_CARDS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

def hand_value(hand: list[str], target: int) -> (int, bool):
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
    while total > target and aces > 0:
        total -= 10
        aces -= 1
    is_busted = total > target
    return (total, is_busted)

@functools.lru_cache(maxsize=None)
def decide(hand_tuple, target):
    hand = list(hand_tuple)
    current_val, is_busted = hand_value(hand, target)
    if is_busted:
        return ("STAY", 0.0)
    if current_val == target:
        return ("STAY", float(target))
    remaining_cards = [c for c in ALL_CARDS if c not in hand_tuple]
    if not remaining_cards:
        return ("STAY", float(current_val))
    hit_values = []
    for card in remaining_cards:
        new_hand = tuple(sorted(hand_tuple + (card,)))
        action, value = decide(new_hand, target)
        hit_values.append(value)
    avg_hit_value = sum(hit_values) / len(remaining_cards)
    if avg_hit_value > current_val:
        return ("HIT", avg_hit_value)
    else:
        return ("STAY", float(current_val))

def policy(hand: list[str], target: int) -> str:
    hand_tuple = tuple(sorted(hand))
    action, _ = decide(hand_tuple, target)
    return action
