
def hand_strength(private_card, public_cards):
    # Simplified evaluation of hand strength for the scenario
    # Evaluates based on the rank of the private and public cards
    ranks = [private_card['rank']] + [card['rank'] for card in public_cards]
    unique_ranks = set(ranks)
    
    # Basic score based on the highest card
    if len(unique_ranks) == 1:
        return 10  # Strongest hand - all cards are of same rank
    elif len(unique_ranks) == 2:
        return 8  # Pair or Two Pair
    elif len(unique_ranks) >= 3:
        return max(ranks)  # High card
    return 0  # No valid hand

def policy(state: dict) -> str:
    my_card = state['private_cards'][0]
    public_cards = state['public_cards']
    my_spent = state['my_spent']
    opponent_spent = state['opponent_spent']
    to_call = state['to_call']
    allowed_actions = state['allowed_actions']
    
    hand_value = hand_strength(my_card, public_cards)
    pot = state['pot']
    
    # Determine action based on the hand value and betting situation
    if 'fold' in allowed_actions and to_call == 0 and pot == 200 and my_spent == 0:
        return 'fold'  # Cannot fold in the very first round with full stacks

    # Decide on action based on hand strength and pot odds
    if hand_value >= 8:  # Strong hand, consider raising
        if 'raise' in allowed_actions:
            return 'raise'
        if 'all-in' in allowed_actions:
            return 'all-in'
    elif hand_value >= 5 and to_call > 0:  # Moderate hand, consider calling
        if 'call' in allowed_actions:
            return 'call'
    elif 'fold' in allowed_actions:
        return 'fold'  # Default fallback to folding otherwise

    return 'call'  # Default to calling if no other legal move
