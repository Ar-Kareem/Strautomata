
import functools

# The full set of cards in a single deck
DECK = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

def get_hand_value(hand_tuple, target):
    """
    Calculates the value of the hand.
    Aces are treated as 11 if the total sum <= target, otherwise 1.
    """
    value = 0
    aces = 0
    
    for card in hand_tuple:
        if card == "A":
            aces += 1
        elif card in ["J", "Q", "K"]:
            value += 10
        else:
            value += int(card)
            
    # Greedily add 11 for Aces to maximize score without busting
    for _ in range(aces):
        if value + 11 <= target:
            value += 11
        else:
            value += 1
            
    return value

@functools.lru_cache(maxsize=None)
def solve_hand(hand_tuple, target):
    """
    Returns the maximum expected score for the given hand and target.
    This function performs a recursive search over the state space.
    """
    current_score = get_hand_value(hand_tuple, target)
    
    # If the current hand is a bust, the value is 0 (loss)
    if current_score > target:
        return 0.0
    
    # Value of staying is the current score
    value_stay = float(current_score)
    
    # Calculate value of hitting
    # Determine remaining cards
    hand_set = set(hand_tuple)
    remaining_cards = [c for c in DECK if c not in hand_set]
    
    # If no cards remain, we must stay
    if not remaining_cards:
        return value_stay
        
    value_hit = 0.0
    for card in remaining_cards:
        # Create the next hand state
        next_hand_list = list(hand_tuple)
        next_hand_list.append(card)
        next_hand_list.sort() # Sort to maintain consistent cache keys
        next_hand_tuple = tuple(next_hand_list)
        
        # Add the expected value of the next state
        value_hit += solve_hand(next_hand_tuple, target)
        
    average_hit = value_hit / len(remaining_cards)
    
    # Return the max of the two options
    return max(value_stay, average_hit)

def policy(hand: list[str], target: int) -> str:
    """
    Determines the next move ('HIT' or 'STAY') based on the current hand and target.
    """
    # Sort input hand for consistency
    current_hand_tuple = tuple(sorted(hand))
    
    # Calculate current score
    current_score = get_hand_value(current_hand_tuple, target)
    
    # If already bust, STAY (though game likely over, we must return a legal string)
    if current_score > target:
        return "STAY"
        
    # Determine remaining cards
    hand_set = set(hand)
    remaining_cards = [c for c in DECK if c not in hand_set]
    
    if not remaining_cards:
        return "STAY"
        
    # Calculate expected value of hitting
    total_expected_hit = 0.0
    for card in remaining_cards:
        next_hand_list = list(current_hand_tuple) + [card]
        next_hand_list.sort()
        next_hand_tuple = tuple(next_hand_list)
        
        # Get optimal expected score from the next state using memoized solver
        next_score = solve_hand(next_hand_tuple, target)
        total_expected_hit += next_score
        
    average_expected_hit = total_expected_hit / len(remaining_cards)
    
    # Decision: HIT if expected value of hitting > current score (value of staying)
    # We add a tiny epsilon to handle potential floating point ambiguities if strictly needed,
    # but standard comparison works for score vs expected score of integers.
    if average_expected_hit > current_score:
        return "HIT"
    else:
        return "STAY"
