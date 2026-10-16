
def evaluate_hand(private_cards, public_cards):
    # A simplified hand evaluation based on rank; more advanced hand evaluations can be implemented
    hand_ranks = [card['rank'] for card in private_cards + public_cards]
    unique_ranks = set(hand_ranks)
    
    # Return strength based on number of unique ranks (the more unique ranks, the weaker the hand: 1 pair, 2 pairs, etc.)
    if len(unique_ranks) == 2:
        return 3  # Full House or Four of a Kind possible
    elif len(unique_ranks) == 3:
        return 2  # Three of a kind or Two Pair possible
    elif len(unique_ranks) == 4:
        return 1  # One Pair
    else:
        return 0  # High Card or worse

def policy(state: dict) -> str:
    private_cards = state['private_cards']
    public_cards = state['public_cards']
    pot = state['pot']
    my_spent = state['my_spent']
    opponent_spent = state['opponent_spent']
    to_call = state['to_call']
    allowed_actions = state['allowed_actions']
    
    hand_strength = evaluate_hand(private_cards, public_cards)
    
    # Define basic raising logic and aggression levels
    if 'all-in' in allowed_actions and (hand_strength > 1 or pot > my_spent):
        return 'all-in'
    elif 'raise' in allowed_actions and (hand_strength >= 2 or pot > (my_spent + to_call)):
        return 'raise'
    elif 'call' in allowed_actions:
        if to_call == 0:
            return 'call'  # Check if we have option to check
        else:
            # Call if we have a decent hand or to see the next card
            if hand_strength >= 1 or pot > (my_spent + to_call):
                return 'call'
    
    return 'fold'  # Default case to fold if none of the above conditions are met
