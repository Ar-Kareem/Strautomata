
import numpy as np

def evaluate_hand_strength(private_cards, public_cards):
    """Evaluate hand strength (simplified) based on ranks and card combinations."""
    # Get ranks of hole cards
    hole_ranks = [card['rank'] for card in private_cards]
    board_ranks = [card['rank'] for card in public_cards]
    
    # Simple hand strength approximation:
    # High card value matters, same rank cards are better
    max_hole_rank = max(hole_ranks)
    has_pair = len(set(hole_ranks)) < len(hole_ranks)
    
    # Check for potential straights/flushes (simplified)
    all_ranks = hole_ranks + board_ranks
    sorted_ranks = sorted(all_ranks)
    
    # Simple straight check (not comprehensive)
    straight = False
    for i in range(len(sorted_ranks) - 4):
        if sorted_ranks[i+4] - sorted_ranks[i] == 4:
            straight = True
            break
    
    # Simple flush check (simplified with suit info)
    # Estimate how many cards we have of a single suit vs total
    board_suits = [card['suit'] for card in public_cards]
    hole_suits = [card['suit'] for card in private_cards]
    all_suits = hole_suits + board_suits
    suit_counts = {}
    for suit in all_suits:
        suit_counts[suit] = suit_counts.get(suit, 0) + 1
    flush_suit = max(suit_counts, key=suit_counts.get) if suit_counts else None
    flush_count = suit_counts.get(flush_suit, 0) if flush_suit else 0
    has_flush = flush_count >= 5
    
    # Hand strength scores:
    # Highest card in hole cards
    score = max_hole_rank
    
    # Bonus for pairs
    if has_pair:
        score += 10
    
    # Bonus for flush
    if has_flush:
        score += 15
    
    # Bonus for straight
    if straight:
        score += 12
    
    # Bonus for high card combo
    if len(hole_ranks) == 2 and hole_ranks[0] == hole_ranks[1]:
        score += 20  # Pairs get big bonus
    elif max_hole_rank >= 10:  # High cards
        score += 5
    
    return score

def policy(state: dict) -> str:
    # Get state information
    private_cards = state['private_cards']
    public_cards = state['public_cards']
    pot = state['pot']
    my_spent = state['my_spent']
    opponent_spent = state['opponent_spent']
    to_call = state['to_call']
    allowed_actions = state['allowed_actions']
    stack = 100 - my_spent  # Assume starting stack is 100
    
    # Evaluate hand strength
    hand_strength = evaluate_hand_strength(private_cards, public_cards)
    
    # Calculate pot odds  
    current_bet = opponent_spent - my_spent
    pot_odds = (pot + current_bet) / (to_call + current_bet) if to_call > 0 else 0
    
    # Basic strategy
    if 'fold' in allowed_actions and to_call > 0:
        # If in early round and both have 100 chips, don't fold
        if pot == 200 and my_spent == 100 and opponent_spent == 100:
            pass  # Don't fold in first round
        else:
            # Early game fold conditions
            if hand_strength < 5 and to_call > stack * 0.4:  # Fold if big bet on weak hand
                return 'fold'
            elif hand_strength < 8 and to_call > stack * 0.3:
                return 'fold'
    
    # Raise if we have a strong hand and can profitably raise
    if 'raise' in allowed_actions and hand_strength >= 15:
        return 'raise'
    
    # All-in if we have a decent hand and we're all-in 
    if 'all-in' in allowed_actions and hand_strength >= 10:
        return 'all-in'
    
    # Call if we have a decent hand or pot odds are good
    if 'call' in allowed_actions:
        # Call if we have decent hand
        if hand_strength >= 8:
            return 'call'
        # Call if pot odds are reasonable 
        if pot_odds > 1.5 and hand_strength >= 5:
            return 'call'
        # Call if no bet to call and weak hand (just check)
        if to_call == 0 and hand_strength < 10:
            return 'call'
        # Call if we have a marginal hand and pot odds reward it
        if to_call <= (stack * 0.1) and hand_strength >= 3:
            return 'call'
    
    # Default behavior if we can check (when no bet)
    if 'call' in allowed_actions and to_call == 0:
        return 'call'
    
    # If we can fold (and are required to) and don't have a good hand
    if 'fold' in allowed_actions and hand_strength < 7 and to_call > 0:
        # If this is the first round and it's the only legal action, don't fold
        if pot >= 200 and my_spent == 100 and opponent_spent == 100:
            return 'call'  # Don't fold in first round
        return 'fold'
    
    # Default to calling if others are legal and we don't have a strong reason to fold/raise
    if 'call' in allowed_actions:
        return 'call'
    
    # If all else fails, just raise if possible
    if 'raise' in allowed_actions:
        return 'raise'
    
    # If all else fails, fold
    return 'fold'
