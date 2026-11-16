
all_cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

def hand_value(hand, target):
    total = 0
    aces = 0
    for card in hand:
        if card == "A":
            total += 11
            aces += 1
        elif card in ["J", "Q", "K"]:
            total += 10
        else:
            total += int(card)
    for _ in range(aces):
        if total > target:
            total -= 10
        else:
            break
    return total

def policy(hand, target):
    remaining_cards = [card for card in all_cards if card not in hand]
    if len(remaining_cards) == 0:
        return "STAY"
    
    H = hand_value(hand, target)
    if H <= target - 10:
        return "HIT"
    
    bust_cards = 0
    for card in remaining_cards:
        new_hand = hand + [card]
        new_value = hand_value(new_hand, target)
        if new_value > target:
            bust_cards += 1
    p_bust = bust_cards / len(remaining_cards)
    
    if p_bust < 0.5:
        return "HIT"
    else:
        return "STAY"
