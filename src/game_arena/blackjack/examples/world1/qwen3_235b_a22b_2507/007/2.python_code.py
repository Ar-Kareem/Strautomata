
def hand_value(hand: list[str], target: int) -> int:
    non_ace = 0
    ace_count = 0
    for card in hand:
        if card == "A":
            ace_count += 1
        elif card in ["J", "Q", "K"]:
            non_ace += 10
        else:
            non_ace += int(card)
    
    total = non_ace
    # Use as many Aces as 11 as possible without exceeding target
    for _ in range(ace_count):
        if total + 11 <= target:
            total += 11
        else:
            total += 1
    return total


def policy(hand: list[str], target: int) -> str:
    current_value = hand_value(hand, target)
    
    # If we've busted or reached target, stay
    if current_value >= target:
        return "STAY"
    
    # If we are very close, stay to avoid risk
    if current_value > target - 2:
        return "STAY"
    
    # Determine remaining cards
    all_cards = {"A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"}
    remaining = all_cards - set(hand)
    
    if not remaining:
        return "STAY"
    
    # Count how many next cards result in a safe hand (not bust)
    safe_count = 0
    for card in remaining:
        new_hand = hand + [card]
        new_value = hand_value(new_hand, target)
        if new_value <= target:
            safe_count += 1
    
    safe_ratio = safe_count / len(remaining)
    
    # Decision based on safety and current deficit
    deficit = target - current_value
    
    if safe_ratio >= 0.6:
        return "HIT"
    elif safe_ratio >= 0.4 and deficit >= 3:
        return "HIT"
    elif safe_ratio >= 0.3 and deficit >= 5:
        return "HIT"
    else:
        return "STAY"
