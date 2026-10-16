
def policy(hand: list[str], target: int) -> str:
    all_cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    
    def compute_hand_value(current_hand, T):
        non_ace_cards = [c for c in current_hand if c != "A"]
        non_ace_sum = sum(
            10 if c in "JQK" else int(c)
            for c in non_ace_cards
        )
        if "A" in current_hand:
            if non_ace_sum + 11 <= T:
                return non_ace_sum + 11
            else:
                return non_ace_sum + 1
        else:
            return non_ace_sum
    
    current_value = compute_hand_value(hand, target)
    
    # If we are at or above target, stay (above should not happen as we bust, but if equal, stay)
    if current_value >= target:
        return "STAY"
    
    # Get remaining cards (not in hand)
    remaining = [c for c in all_cards if c not in hand]
    if not remaining:
        return "STAY"
    
    # Compute expected value of the hand after one hit and then staying
    total_future_value = 0.0
    for card in remaining:
        new_hand = hand + [card]
        new_value = compute_hand_value(new_hand, target)
        if new_value > target:
            # Bust: this is very bad, so we assign a very low value
            total_future_value += -1000.0
        else:
            total_future_value += new_value
    
    expected_future_value = total_future_value / len(remaining)
    
    # If the expected value after hitting is better than current, then hit
    if expected_future_value > current_value:
        return "HIT"
    else:
        return "STAY"
