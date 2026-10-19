
def calculate_sum(hand: list[str], target: int) -> int:
    fixed_sum = 0
    ace_count = 0
    for card in hand:
        if card == 'A':
            ace_count += 1
        elif card in ['J', 'Q', 'K']:
            fixed_sum += 10
        else:
            fixed_sum += int(card)
    sum_minimal = fixed_sum + ace_count  # All aces as 1
    if sum_minimal > target:
        return float('inf')  # Indicates a bust
    
    allowed_additional = target - sum_minimal
    if allowed_additional < 0:
        return sum_minimal
    
    num_convert = min(ace_count, allowed_additional // 10)
    return sum_minimal + num_convert * 10

def policy(hand: list[str], target: int) -> str:
    current_sum = calculate_sum(hand, target)
    if current_sum > target:
        return 'STAY'  # Already busted
    
    all_ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    remaining = [card for card in all_ranks if card not in hand]
    if not remaining:
        return 'STAY'
    
    total_gain = 0.0
    total_carves = 0
    bust_count = 0
    
    for card in remaining:
        new_hand = hand.copy()
        new_hand.append(card)
        new_sum = calculate_sum(new_hand, target)
        if new_sum > target:
            bust_count += 1
        else:
            delta = new_sum - current_sum
            if delta > 0:
                total_gain += delta
                total_carves += 1
    
    if total_carves == 0:
        return 'STAY'
    avg_gain = total_gain / total_carves if total_carves else 0.0
    if avg_gain > 0:
        return 'HIT'
    else:
        return 'STAY'
