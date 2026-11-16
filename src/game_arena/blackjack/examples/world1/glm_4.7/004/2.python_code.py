
def policy(hand: list[str], target: int) -> str:
    """
    Smart policy for simplified Blackjack game.
    
    Strategy: Maximize expected win probability by comparing the expected
    win probability of hitting vs staying. The expected win probability of
    a hand value v is assumed to be proportional to v / target (assuming
    the opponent is equally likely to score any value from 0 to target).
    """
    all_cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    
    def card_value(card):
        if card in ["J", "Q", "K"]:
            return 10
        elif card == "A":
            return 11
        else:
            return int(card)
    
    def hand_value(hand):
        """Calculate the value of a hand, handling Aces correctly."""
        val = sum(card_value(c) for c in hand)
        ace_count = hand.count("A")
        # Convert Aces from 11 to 1 as needed to avoid busting
        while val > target and ace_count > 0:
            val -= 10
            ace_count -= 1
        return val
    
    current_val = hand_value(hand)
    
    # If already busted, stay
    if current_val > target:
        return "STAY"
    
    # Find remaining cards in deck
    used_cards = set(hand)
    remaining_cards = [c for c in all_cards if c not in used_cards]
    
    if not remaining_cards:
        return "STAY"
    
    # Calculate expected win probability of hitting
    win_prob_sum = 0
    
    for card in remaining_cards:
        new_hand = hand + [card]
        new_val = hand_value(new_hand)
        if new_val <= target:
            # Win probability is proportional to hand value
            win_prob_sum += new_val / target
        # If new_val > target, we bust and win_prob is 0
    
    expected_hit_win_prob = win_prob_sum / len(remaining_cards)
    current_win_prob = current_val / target
    
    # HIT if expected hit win probability is strictly better
    if expected_hit_win_prob > current_win_prob:
        return "HIT"
    
    return "STAY"
