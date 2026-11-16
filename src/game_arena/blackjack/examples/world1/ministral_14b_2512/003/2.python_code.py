
def policy(hand: list[str], target: int) -> str:
    def calculate_hand_value(h, t):
        sum_val = 0
        aces = 0
        for card in h:
            if card == "A":
                sum_val += 11
                aces += 1
            elif card in ["J", "Q", "K"]:
                sum_val += 10
            else:  # 2-10
                sum_val += int(card)

        # Adjust for Aces if sum > t
        while sum_val > t and aces > 0:
            sum_val -= 10
            aces -= 1
        return sum_val

    current_sum = calculate_hand_value(hand, target)

    if current_sum >= target:
        return "STAY"
    if current_sum + 2 > target:
        return "STAY"
    else:
        return "HIT"
