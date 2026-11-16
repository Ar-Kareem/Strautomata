
def policy(hand: list[str], target: int) -> str:
    """
    A simple Blackjack policy.

    Args:
        hand: A list of strings representing the cards in hand.
        target: The target score to approach.

    Returns:
        "HIT" or "STAY" depending on the policy.
    """

    def hand_value(hand):
        total = 0
        aces = 0
        for card in hand:
            if card.isdigit():
                total += int(card)
            elif card in ("J", "Q", "K"):
                total += 10
            elif card == "A":
                aces += 1
        
        for _ in range(aces):
            if total + 11 <= target:
                total += 11
            else:
                total += 1
        return total

    current_value = hand_value(hand)

    if current_value > target:
        return "STAY"  # Already busted

    if current_value <= target - 5:
        return "HIT"

    if current_value <= target - 3:
        # Check hit chance with Ace is low:
        num_hit_cards = 13 - len(hand)
        expected_value_increase = 0
        for i in range(2, 11):
             prob_i = (1 / num_hit_cards) if num_hit_cards > 0 else 0
             if current_value + i <= target:
                 expected_value_increase += prob_i * i  
        prob_face = (3 / num_hit_cards) if num_hit_cards > 0 else 0
        if current_value + 10 <= target:
                expected_value_increase += prob_face * 10
        prob_ace = (1 / num_hit_cards) if num_hit_cards > 0 else 0   
        
        if current_value + 11 <= target:
            expected_value_increase_with_ace = expected_value_increase +prob_ace *11
        else:
            expected_value_increase_with_ace = expected_value_increase +prob_ace * 1

        if expected_value_increase_with_ace <= target- current_value:
            return "HIT"

    return "STAY"
