
def policy(hand: list[str], target: int) -> str:
    def calculate_max_sum(hand, target):
        sum_non_ace = 0
        num_aces = 0
        for card in hand:
            if card == 'A':
                num_aces += 1
            elif card in ['J', 'Q', 'K']:
                sum_non_ace += 10
            elif card == '10':
                sum_non_ace += 10
            else:
                sum_non_ace += int(card)
        max_possible = sum_non_ace + 11 * num_aces
        if max_possible <= target:
            return max_possible
        else:
            overflow = max_possible - target
            required = min(num_aces, (overflow + 9) // 10)
            return sum_non_ace + 11 * (num_aces - required) + 1 * required

    all_cards = {'A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K'}

    current_sum = calculate_max_sum(hand, target)
    if current_sum == target:
        return 'STAY'

    remaining_cards = all_cards - set(hand)
    for card in remaining_cards:
        new_hand = hand + [card]
        new_sum = calculate_max_sum(new_hand, target)
        if new_sum <= target and new_sum > current_sum:
            return 'HIT'

    return 'STAY'
