
def hand_value(hand, target):
    sum_without_ace = 0
    has_ace = False
    for card in hand:
        if card == "A":
            has_ace = True
        else:
            if card in ["J", "Q", "K"]:
                sum_without_ace += 10
            else:
                sum_without_ace += int(card)
    if has_ace:
        if sum_without_ace + 11 <= target:
            return sum_without_ace + 11
        else:
            return sum_without_ace + 1
    else:
        return sum_without_ace

def policy(hand, target):
    S = hand_value(hand, target)
    if "A" in hand:
        if S < target:
            return "HIT"
        else:
            return "STAY"
    else:
        if S < target - 1:
            return "HIT"
        else:
            return "STAY"
