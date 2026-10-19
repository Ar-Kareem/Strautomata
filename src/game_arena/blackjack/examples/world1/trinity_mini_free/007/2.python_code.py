
def policy(hand: list[str], target: int) -> str:
    # Calculate non-Ace card values and count Aces
    non_ace_sum = 0
    ace_count = 0
    for card in hand:
        if card == 'A':
            ace_count += 1
        elif card in ['J', 'Q', 'K']:
            non_ace_sum += 10
        else:
            non_ace_sum += int(card)
    
    # Calculate maximum possible total without busting
    total = non_ace_sum + 11 * ace_count
    if total > target:
        # Adjust Aces from 11 to 1 if total exceeds target
        k = (total - target + 9) // 10
        total = total - 10 * k
    
    # Dynamic threshold: hit if total is below (target - 5)
    if total < target - 5:
        return "HIT"
    else:
        return "STAY"
