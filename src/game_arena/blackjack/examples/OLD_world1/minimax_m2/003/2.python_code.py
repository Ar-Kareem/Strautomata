
def compute_hand_value(hand, target):
    num_aces = hand.count("A")
    value = 11 * num_aces
    for card in hand:
        if card != "A":
            if card in ["2", "3", "4", "5", "6", "7", "8", "9", "10"]:
                value += int(card)
            elif card in ["J", "Q", "K"]:
                value += 10
    while value > target and num_aces > 0:
        value -= 10
        num_aces -= 1
    return value

def policy(hand: list[str], target: int) -> str:
    current_value = compute_hand_value(hand, target)
    
    # If already busted or exactly at target, stay
    if current_value > target:
        return "STAY"
    if current_value == target:
        return "STAY"
    
    # Define the deck and remaining cards
    deck = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    remaining_deck = [card for card in deck if card not in hand]
    
    # If no cards left, must stay
    if len(remaining_deck) == 0:
        return "STAY"
    
    total = 0.0
    for card in remaining_deck:
        new_hand = hand + [card]
        new_value = compute_hand_value(new_hand, target)
        if new_value > target:
            # Very low value for bust to discourage risky hits
            total += -10000.0
        else:
            total += new_value
    
    expected_value = total / len(remaining_deck)
    
    if expected_value > current_value:
        return "HIT"
    else:
        return "STAY"
