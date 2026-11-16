
import collections

def get_hand_value(hand: list[str], target: int) -> int:
    """Calculates the highest hand value that does not exceed target, if possible."""
    val = 0
    aces = 0
    card_map = {
        "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,
        "10": 10, "J": 10, "Q": 10, "K": 10, "A": 11
    }
    
    for card in hand:
        if card == "A":
            aces += 1
        val += card_map[card]
    
    while val > target and aces > 0:
        val -= 10
        aces -= 1
    return val

def policy(hand: list[str], target: int) -> str:
    """
    Determines whether to HIT or STAY based on the remaining cards in the deck
     and the probability of busting.
    """
    if not hand:
        return "HIT"
    
    current_value = get_hand_value(hand, target)
    
    # If we are already at or above target (shouldn't happen if logic is right), STAY
    if current_value >= target:
        return "STAY"
    
    # Define the full deck
    full_deck = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    
    # Remove cards already in hand from the pool
    remaining_deck = full_deck[:]
    for card in hand:
        if card in remaining_deck:
            remaining_deck.remove(card)
    
    if not remaining_deck:
        return "STAY"
    
    # Calculate how many cards in the remaining deck would cause a bust
    bust_count = 0
    for next_card in remaining_deck:
        new_hand = hand + [next_card]
        if get_hand_value(new_hand, target) > target:
            bust_count += 1
            
    bust_prob = bust_count / len(remaining_deck)
    
    # Heuristic: 
    # If target is high (30), we need to be more aggressive.
    # If target is low (10), we are very restricted.
    # Generally, STAY if the probability of busting is > 40-50% 
    # OR if we are within a very safe margin of the target.
    
    # If chance of busting is low, HIT.
    if bust_prob < 0.45:
        # Extra check: if we are only 1 or 2 away from target, don't risk it 
        # unless there are cards in the deck that can actually help.
        if current_value >= target - 2:
            # Only hit if there's a card that gets us exactly to target
            exact_hits = 0
            for next_card in remaining_deck:
                if get_hand_value(hand + [next_card], target) == target:
                    exact_hits += 1
            if exact_hits > 0:
                return "HIT"
            return "STAY"
        return "HIT"
    
    return "STAY"

