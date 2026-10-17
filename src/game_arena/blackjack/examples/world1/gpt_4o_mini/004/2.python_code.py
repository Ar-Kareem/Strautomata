
def policy(hand: list[str], target: int) -> str:
    def card_value(card: str) -> int:
        if card in ["J", "Q", "K"]:
            return 10
        elif card == "A":
            return 11  # Temporarily assume Aces are worth 11
        else:
            return int(card)

    def evaluate_hand(hand: list[str]) -> int:
        total = sum(card_value(card) for card in hand)
        aces_count = hand.count("A")
        
        # Adjust for Aces
        while total > target and aces_count > 0:
            total -= 10  # Count Ace as 1 instead of 11
            aces_count -= 1
        
        return total

    current_value = evaluate_hand(hand)

    if current_value > target:
        return "STAY"  # If we bust already, do nothing
    elif current_value >= target - 5:
        return "STAY"  # Close to target; safer to stay
    elif current_value < target - 10:
        return "HIT"  # Much lower than target; hit is safer
    else:
        return "HIT"  # In balanced region, we lean towards hitting
