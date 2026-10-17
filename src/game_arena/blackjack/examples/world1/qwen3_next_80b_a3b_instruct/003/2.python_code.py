
def policy(hand: list[str], target: int) -> str:
    def calculate_hand_value(hand, target):
        non_ace_sum = 0
        num_aces = 0
        for card in hand:
            if card == "A":
                num_aces += 1
            else:
                if card == "J" or card == "Q" or card == "K":
                    non_ace_sum += 10
                else:
                    non_ace_sum += int(card)
        base = non_ace_sum + num_aces
        if base > target:
            return base
        k = min(num_aces, (target - base) // 10)
        return base + 10 * k

    current_value = calculate_hand_value(hand, target)
    if current_value >= target - 3:
        return "STAY"
    else:
        return "HIT"
