
def policy(hand: list[str], target: int) -> str:
    def hand_value(cards, t):
        total = 0
        aces = 0
        for card in cards:
            if card in ['J', 'Q', 'K']:
                total += 10
            elif card == 'A':
                aces += 1
                total += 11
            else:
                total += int(card)
        while total > t and aces:
            total -= 10
            aces -= 1
        return total

    s = hand_value(hand, target)
    if s > target:
        return "STAY"
    if s == target:
        return "STAY"

    all_cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    available = [card for card in all_cards if card not in hand]

    if not available:
        return "STAY"

    bust_count = 0
    expected_sum = 0
    non_bust_count = 0

    for card in available:
        new_hand = hand + [card]
        new_val = hand_value(new_hand, target)
        if new_val > target:
            bust_count += 1
        else:
            expected_sum += new_val
            non_bust_count += 1

    if non_bust_count == 0:
        return "STAY"
    expected_avg = expected_sum / non_bust_count

    return "HIT" if expected_avg > s else "STAY"
