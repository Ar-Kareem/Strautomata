
def policy(hand: list[str], target: int) -> str:
    def calculate_total(h, t):
        sum_non_ace = 0
        has_ace = False
        for card in h:
            if card == "A":
                has_ace = True
            else:
                if card in ["J", "Q", "K"]:
                    sum_non_ace += 10
                else:
                    sum_non_ace += int(card)
        if has_ace:
            tentative = sum_non_ace + 11
            if tentative <= t:
                return tentative
            else:
                return sum_non_ace + 1
        else:
            return sum_non_ace
    
    total = calculate_total(hand, target)
    if total >= target:
        return "STAY"
    if total + 1 <= target:
        return "HIT"
    else:
        return "STAY"
