
def policy(hand: list[str], target: int) -> str:
    def calculate_best_sum(hand, target):
        non_aces = []
        num_aces = 0
        for card in hand:
            if card == "A":
                num_aces += 1
            else:
                if card in {"J", "Q", "K"}:
                    non_aces.append(10)
                elif card == "10":
                    non_aces.append(10)
                else:
                    non_aces.append(int(card))
        non_ace_sum = sum(non_aces)
        max_with_aces = non_ace_sum + num_aces * 11
        if max_with_aces <= target:
            return max_with_aces
        else:
            diff = max_with_aces - target
            required_conversions = (diff + 9) // 10  # ceil division
            if required_conversions > num_aces:
                return None  # bust
            else:
                return max_with_aces - required_conversions * 10

    # Compute current best sum
    current_best = calculate_best_sum(hand, target)
    if current_best is None:
        return "STAY"
    current_distance = abs(target - current_best)
    
    # Compute remaining cards
    all_cards = {"A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"}
    remaining = list(all_cards - set(hand))
    if not remaining:
        return "STAY"
    
    # Penalty for bust (a large number)
    PENALTY = target + 1000
    total_next_distance = 0.0
    for card in remaining:
        new_hand = hand + [card]
        new_best = calculate_best_sum(new_hand, target)
        if new_best is None:
            total_next_distance += PENALTY
        else:
            total_next_distance += abs(target - new_best)
    
    average_next_distance = total_next_distance / len(remaining)
    
    # Decide based on whether hitting improves the distance on average
    return "HIT" if average_next_distance < current_distance else "STAY"
