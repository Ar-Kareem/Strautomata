
ALL_CARDS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

def hand_value(hand, target):
    total = 0
    aces = 0
    for card in hand:
        if card == 'A':
            aces += 1
        elif card in ['J', 'Q', 'K']:
            total += 10
        else:
            total += int(card)
    for _ in range(aces):
        if total + 11 <= target:
            total += 11
        else:
            total += 1
    return total

def policy(hand: list[str], target: int) -> str:
    current_sum = hand_value(hand, target)
    available_cards = [c for c in ALL_CARDS if c not in hand]
    non_bust_cards_sum = 0.0
    non_bust_count = 0
    for card in available_cards:
        new_hand = hand + [card]
        new_sum = hand_value(new_hand, target)
        if new_sum <= target:
            non_bust_cards_sum += new_sum
            non_bust_count += 1
    if non_bust_count == 0:
        return "STAY"
    average_new_sum = non_bust_cards_sum / non_bust_count
    if average_new_sum > current_sum:
        return "HIT"
    else:
        return "STAY"
