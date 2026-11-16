
import random

def policy(state: dict) -> str:
    # Extract state variables
    hole_card = state['private_cards'][0]
    rank = hole_card['rank']
    to_call = state['to_call']
    allowed = state['allowed_actions']
    pot = state['pot']
    public_cards = state['public_cards']
    
    # Calculate hand strength relative to board
    is_top_pair = True
    if public_cards:
        for card in public_cards:
            if card['rank'] > rank:
                is_top_pair = False
                break
    
    # Simple strategy thresholds
    # Rank range is assumed 0-12 (13 cards)
    
    # 1. High Strength: Ranks 10, 11, 12 (Jack, Queen, King, Ace equivalents)
    if rank >= 10 or (public_cards and is_top_pair and rank >= 8):
        if 'raise' in allowed and random.random() < 0.7:
            return 'raise'
        if 'all-in' in allowed and rank == 12:
            return 'all-in'
        return 'call'
    
    # 2. Medium Strength: Ranks 6, 7, 8, 9
    if rank >= 6:
        if to_call > pot * 0.5: # If opponent bets huge
            if rank >= 8:
                return 'call'
            return 'fold' if 'fold' in allowed else 'call'
        return 'call'
    
    # 3. Low Strength: Ranks 0 - 5
    if to_call == 0:
        return 'call' # Check
    
    # Pot odds calculation: if it's cheap to stay in, stay in
    pot_odds = to_call / (pot + to_call)
    if pot_odds < 0.2: # Very cheap to call
        return 'call'
        
    # If the opponent is aggressive and we have a weak hand, fold
    if to_call > 0 and 'fold' in allowed:
        # Never fold if it's the very first round (rule requirement)
        if state['my_spent'] <= 100 and state['opponent_spent'] <= 100:
            return 'call'
        return 'fold'

    return 'call'
