
def policy(state):
    # Extract hole card rank
    hole_card = state['private_cards'][0]
    h_rank = hole_card['rank']
    # Calculate hand strength as probability of winning against a random opponent
    hs = (h_rank - 1) / 13.0
    # Ensure hs is within bounds [0, 1]
    hs = max(0.0, min(1.0, hs))

    pot = state['pot']
    to_call = state['to_call']
    allowed_actions = state['allowed_actions']

    if to_call > 0:
        # Calculate pot odds and call threshold
        pot_odds = pot / to_call
        call_threshold = 1 / (1 + pot_odds)
        raise_threshold = call_threshold + 0.2
        allin_threshold = 0.9

        if hs > allin_threshold:
            if 'all-in' in allowed_actions:
                return 'all-in'
            elif 'raise' in allowed_actions:
                return 'raise'
            elif 'call' in allowed_actions:
                return 'call'
            else:
                return 'fold'
        elif hs > raise_threshold:
            if 'raise' in allowed_actions:
                return 'raise'
            elif 'all-in' in allowed_actions:
                return 'all-in'
            elif 'call' in allowed_actions:
                return 'call'
            else:
                return 'fold'
        elif hs > call_threshold:
            if 'call' in allowed_actions:
                return 'call'
            elif 'fold' in allowed_actions:
                return 'fold'
            else:
                # Fallback if call not allowed but other actions are
                if 'raise' in allowed_actions:
                    return 'raise'
                elif 'all-in' in allowed_actions:
                    return 'all-in'
                elif 'fold' in allowed_actions:
                    return 'fold'
                else:
                    return 'call'  # Should not reach here if actions exist
        else:
            if 'fold' in allowed_actions:
                return 'fold'
            elif 'call' in allowed_actions:
                return 'call'
            else:
                return 'raise'
    else:  # to_call == 0
        if hs > 0.8:
            if 'raise' in allowed_actions:
                return 'raise'
            elif 'all-in' in allowed_actions:
                return 'all-in'
            elif 'call' in allowed_actions:
                return 'call'
            else:
                return 'fold'
        elif hs > 0.5:
            if 'call' in allowed_actions:
                return 'call'
            elif 'fold' in allowed_actions:
                return 'fold'
            else:
                return 'raise'
        else:
            if 'call' in allowed_actions:
                return 'call'
            elif 'fold' in allowed_actions:
                return 'fold'
            else:
                return 'raise'
