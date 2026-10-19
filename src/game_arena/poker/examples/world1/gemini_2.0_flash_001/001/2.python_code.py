
import random

def policy(state: dict) -> str:
    """
    A simple poker AI policy.
    """
    private_card = state['private_cards'][0]
    rank = private_card['rank']
    suit = private_card['suit']
    pot = state['pot']
    my_spent = state['my_spent']
    opponent_spent = state['opponent_spent']
    to_call = state['to_call']
    allowed_actions = state['allowed_actions']
    public_cards = state['public_cards']

    num_public_cards = len(public_cards)

    # Simple hand strength evaluation based on rank
    if rank >= 12:  # Ace, King
        hand_strength = 0.9
    elif rank >= 9:  # Queen, Jack, 10
        hand_strength = 0.6
    elif rank >= 6: # 7, 8, 9
        hand_strength = 0.4
    else:
        hand_strength = 0.2


    # Adjust hand strength based on public cards (simplistic)
    if num_public_cards > 0:
        for card in public_cards:
            if card['rank'] > 12:
                hand_strength -= 0.1  # Deduct strength if high cards are on the board.
            elif card['rank'] >= 9:
                hand_strength -= 0.05

    # Basic pre-flop strategy
    if num_public_cards == 0:
        if rank >= 12:
            if 'raise' in allowed_actions:
                return 'raise'
            elif 'all-in' in allowed_actions:
                return 'all-in'
            elif 'call' in allowed_actions:
                return 'call'
            else:
                return 'fold'
        elif rank >= 8:
            if to_call <= pot * 0.3 and 'call' in allowed_actions : #if call is relatively small for pot size
                return 'call'
            elif 'call' in allowed_actions and to_call == 0:
                return 'call'
            elif 'raise' in allowed_actions :
                return 'raise'
            else:
                return 'fold'
                
        else:
            if to_call == 0 and 'call' in allowed_actions:
                return 'call' #Check if possible
            elif to_call <= pot * 0.1 and 'call' in allowed_actions:
                return 'call'
            elif 'fold' in allowed_actions:
                return 'fold'
            elif 'call' in allowed_actions:
                return 'call' #Last resort
            else: return 'all-in'

    # Post-flop strategy
    else:
        if hand_strength > 0.7:
            if 'raise' in allowed_actions:
                return 'raise'
            elif 'all-in' in allowed_actions:
                return 'all-in'
            elif 'call' in allowed_actions:
                return 'call'
            else:
                return 'fold'
        elif hand_strength > 0.4:
            if to_call <= pot * 0.5 and 'call' in allowed_actions:
                return 'call'
            elif to_call == 0 and 'call' in allowed_actions:
                return 'call'
            elif 'raise' in allowed_actions:
                return 'raise'
            else:
                if 'fold' in allowed_actions:
                    return 'fold'
                elif 'call' in allowed_actions:
                    return 'call'
                else:
                    return 'all-in'
        else:
            if to_call > pot * 0.2 or 'fold' in allowed_actions: #If the price is high and can fold - fold
                if 'fold' in allowed_actions:
                    return 'fold'
                elif 'call' in allowed_actions:
                    return 'call'
                else:
                    return 'all-in'
            elif to_call == 0 and 'call' in allowed_actions:
                return 'call'
            elif 'call' in allowed_actions:
                return 'call' #Calling relatively cheap bet
            elif 'all-in' in allowed_actions:
                return 'all-in'
            else:
                return 'fold' #Last resort



    if 'call' in allowed_actions:
        return 'call'
    elif 'raise' in allowed_actions:
        return 'raise'
    elif 'all-in' in allowed_actions:
        return 'all-in'
    else:
        return 'fold'
