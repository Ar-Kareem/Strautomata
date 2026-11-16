
import random

def policy(state: dict) -> str:
    private_cards = state['private_cards']
    public_cards = state['public_cards']
    pot = state['pot']
    my_spent = state['my_spent']
    opponent_spent = state['opponent_spent']
    to_call = state['to_call']
    allowed_actions = state['allowed_actions']

    my_rank = private_cards[0]['rank']
    
    #if len(public_cards) == 0 and 'fold' in allowed_actions and my_spent==0 and opponent_spent==0 and pot==2:
    #   return 'call'   
    
    if 'all-in' in allowed_actions and random.random() < 0.01: #Small random chance to go all in regardless
         return 'all-in'

    if len(public_cards) == 0:  # Pre-flop strategy
        if my_rank >= 12:  # Ace, King, Queen
            if 'raise' in allowed_actions:
                if random.random() < 0.8 :
                      return 'raise'
                else:
                    return 'call'
            elif 'call' in allowed_actions:
                return 'call'
        elif my_rank >= 8:  # 8 or higher
            if 'call' in allowed_actions:
                  if random.random() > 0.3:
                       return 'call'
                  elif 'fold' in allowed_actions:  
                       return 'fold' #small chance to fold medium hand to add variance
                  else:
                        return 'call'
            elif 'fold' in allowed_actions:
                return 'fold' #fold if we cant call
        else:  # Low rank
            if 'call' in allowed_actions and to_call <= 5: #only call with very low bets.
                   if random.random() < 0.2: #Very infrequent calls
                      return 'call'

            if 'fold' in allowed_actions:
                return 'fold'
            elif 'call' in allowed_actions:
                return 'call' #If we can't fold, call for the edge case where its not allowed to fold.
    else:  # Post-flop strategy
        # Simple hand evaluation (pair or better)
        all_cards = private_cards + public_cards
        ranks = [card['rank'] for card in all_cards]
        rank_counts = {}
        for rank in ranks:
            rank_counts[rank] = rank_counts.get(rank, 0) + 1

        has_pair = False
        for rank, count in rank_counts.items():
            if count >= 2:
                has_pair = True
                break

        if has_pair:
            if 'raise' in allowed_actions:
                if random.random() < 0.7:
                    return 'raise'
                else:
                    return 'call'
            elif 'call' in allowed_actions:
                return 'call'
        else:
            #if opponent_spent > 5 and 'fold' in allowed_actions:
            #    return 'fold'

            if 'call' in allowed_actions and to_call <= 10: #Small bet with nothing, make a reluctant call.
                return 'call'

            if 'fold' in allowed_actions:
                return 'fold'
            elif 'call' in allowed_actions:
                return 'call'

    # Default action (should not be reached, but included for safety)
    if 'call' in allowed_actions:
        return 'call'
    elif 'raise' in allowed_actions:
        return 'raise'
    elif 'all-in' in allowed_actions:
        return 'all-in'
    else:
        return 'fold' # If all else fails and fold is an option, fold. If not, this should never occur.
