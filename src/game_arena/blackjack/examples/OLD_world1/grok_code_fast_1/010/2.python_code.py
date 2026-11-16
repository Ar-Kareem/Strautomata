
def policy(hand: list[str], target: int) -> str:
    def get_value(h, t):
        value_dict = {'2':2, '3':3, '4':4, '5':5, '6':6, '7':7, '8':8, '9':9, '10':10, 'J':10, 'Q':10, 'K':10, 'A':11}
        total = sum(value_dict.get(card, 0) for card in h)
        aces = h.count('A')
        for _ in range(aces):
            if total > t:
                total -= 10
        return total
    
    v = get_value(hand, target)
    if v > target:
        return "STAY"
    
    remaining = [c for c in ['A','2','3','4','5','6','7','8','9','10','J','Q','K'] if c not in hand]
    if not remaining:
        return "STAY"
    
    exp = 0
    for c in remaining:
        new_hand = hand + [c]
        new_v = get_value(new_hand, target)
        if new_v > target:
            new_score = -10
        else:
            new_score = new_v
        exp += new_score
    exp /= len(remaining)
    
    if exp > v:
        return "HIT"
    else:
        return "STAY"
