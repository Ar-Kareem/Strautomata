
import random

def evaluate_hand(private_cards, public_cards):
    """
    A simplified hand evaluation function.  This is a placeholder and could be
    significantly improved with a more comprehensive poker hand ranking algorithm.
    """
    all_cards = private_cards + public_cards
    if not all_cards:
        return 0  # No cards, very weak

    ranks = [card['rank'] for card in all_cards]
    suits = [card['suit'] for card in all_cards]
    
    # Check for pairs.
    if len(private_cards) == 1:
      num_pairs = ranks.count(ranks[0])
      if num_pairs == 1 and len(public_cards) == 0:
          #Initial hand value based on rank
          return ranks[0]
          
      if num_pairs == 1 and len(public_cards) > 0:
          #Pair made on the board
          if ranks.count(public_cards[0]['rank']) == 1:
            return ranks[0]  #Only initial card
        
      if num_pairs > 1:
          #Pair has been made
          return ranks[0] * 2

    highest_rank = max(ranks)
    return highest_rank


def policy(state: dict) -> str:
    """
    A poker policy that considers hand strength, pot odds, and a bit of bluffing.
    """
    private_cards = state['private_cards']
    public_cards = state['public_cards']
    pot = state['pot']
    my_spent = state['my_spent']
    opponent_spent = state['opponent_spent']
    to_call = state['to_call']
    allowed_actions = state['allowed_actions']

    hand_strength = evaluate_hand(private_cards, public_cards)

    # Pot odds calculation
    if to_call > 0:
        pot_odds = to_call / (pot + to_call)
    else:
        pot_odds = 0

    # Basic strategy
    if 'raise' in allowed_actions and to_call <=0 :
        if hand_strength > 10:
            return 'raise'
        elif hand_strength > 5 and random.random() < 0.3 :
            return 'raise'

    if 'call' in allowed_actions and to_call > 0:
        if hand_strength > 5 or pot_odds < 0.3:
            return 'call'
        elif random.random() < 0.1 and pot > 150:
                return 'call' #Bluff call sometimes in later rounds.

    if 'all-in' in allowed_actions:
        if hand_strength > 12:
            return 'all-in'
        elif hand_strength >8 and random.random() < 0.2:
            return 'all-in'

    if 'fold' in allowed_actions:
        if hand_strength < 5 and to_call > 10:
            return 'fold'

    if 'call' in allowed_actions:
      return 'call'  # Default to call

    # If no other actions available, and can't call then fold.
    if 'fold' in allowed_actions:
      return 'fold'

    return 'call' #Should not get here, but include as safe default
