
def policy(state: dict) -> str:
    # Check if folding is allowed and hand is weak
    if 'fold' in state['allowed_actions']:
        # First round (no public cards) with low hole card rank
        if len(state['public_cards']) == 0:
            if state['private_cards'][0]['rank'] < 10:
                return 'fold'
        # Later rounds with no matching public card
        else:
            hole_rank = state['private_cards'][0]['rank']
            if not any(card['rank'] == hole_rank for card in state['public_cards']):
                return 'fold'
    
    # Evaluate hand strength for calling/raising
    hole_rank = state['private_cards'][0]['rank']
    public_ranks = [card['rank'] for card in state['public_cards']]
    
    # Check for a pair (hole card matches public card)
    if hole_rank in public_ranks:
        # Call if affordable or go all-in if allowed
        if state['to_call'] <= state['my_spent']:
            return 'call'
        elif 'all-in' in state['allowed_actions']:
            return 'all-in'
    
    # Default to folding for unpaired hands
    return 'fold'
