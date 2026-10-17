
def policy(state: dict) -> str:
    import random

    # Basic data extraction
    my_card = state['private_cards'][0]
    rank = my_card['rank']
    allowed = state['allowed_actions']
    to_call = state['to_call']
    pot = state['pot']
    
    # Normalize rank: Assuming 2-14 (Ace high)
    # Strength 0.0 to 1.0
    strength = (rank - 2) / 12.0
    
    # Check if we have the nuts or a very strong hand relative to board
    if state['public_cards']:
        max_pub = max(c['rank'] for c in state['public_cards'])
        if rank > max_pub:
            strength += 0.2
        elif rank < max_pub:
            strength -= 0.1
    
    strength = min(1.0, max(0.0, strength))
    
    # Calculate Pot Odds: how much we pay vs how much we can win
    # if to_call / (pot + to_call) is low, it's a "cheap" call
    pot_odds = to_call / (pot + to_call) if (pot + to_call) > 0 else 0
    
    # Decision Logic
    action = 'call' # Default
    
    if strength > 0.85:
        # Very strong: look for value
        if 'all-in' in allowed and (pot > 500 or strength > 0.95):
            action = 'all-in'
        elif 'raise' in allowed:
            action = 'raise'
        else:
            action = 'call'
            
    elif strength > 0.6:
        # Good hand: call or raise
        if 'raise' in allowed and random.random() < 0.3:
            action = 'raise'
        else:
            action = 'call'
            
    elif strength > 0.3:
        # Mediocre hand: call if cheap
        if to_call == 0:
            action = 'call'
        elif pot_odds < 0.3:
            action = 'call'
        else:
            action = 'fold'
            
    else:
        # Weak hand: fold unless checking is free
        if to_call == 0:
            action = 'call'
        else:
            action = 'fold'

    # Final validation: Ensure selected action is legal
    if action not in allowed:
        if action == 'all-in' and 'raise' in allowed:
            action = 'raise'
        elif action == 'raise' and 'call' in allowed:
            action = 'call'
        elif action == 'fold' and 'call' in allowed:
            # Never fold if we can check (to_call == 0)
            if to_call == 0:
                action = 'call'
            else:
                # If fold is not allowed (start of game rule), must call
                action = 'call'
        else:
            action = allowed[0]

    return action
