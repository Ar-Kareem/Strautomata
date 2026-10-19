
import random
import math
from collections import defaultdict

# Pre-flop hand strength lookup for single card
PREFLOP_RANK = {
    14: 1.0,  # Ace
    13: 0.85, # King
    12: 0.75, # Queen
    11: 0.65, # Jack
    10: 0.6,  # Ten
    9: 0.55,  # Nine
    8: 0.5,   # Eight
    7: 0.45,  # Seven
    6: 0.4,   # Six
    5: 0.35,  # Five
    4: 0.3,   # Four
    3: 0.25,  # Three
    2: 0.2,   # Two
}

SUIT_BONUS = 0.02  # small bonus for suited boards (not used heavily here)

def estimate_hand_strength(private_cards, public_cards, opponent_range=None, n_sim=200):
    """
    Estimate win probability via Monte Carlo simulation.
    """
    if not public_cards:
        # Pre-flop: use lookup table
        card = private_cards[0]
        return PREFLOP_RANK.get(card['rank'], 0.5)
    
    # Simple heuristic for post-flop: rank + flush/straight potential
    my_rank = private_cards[0]['rank']
    my_suit = private_cards[0]['suit']
    
    # Count suited public cards
    suited_public = sum(1 for c in public_cards if c['suit'] == my_suit)
    flush_potential = suited_public / max(1, len(public_cards))
    
    # High card potential
    high_card_strength = my_rank / 14.0
    
    # Pair potential
    pair_potential = any(c['rank'] == my_rank for c in public_cards)
    
    # Rough estimate
    strength = 0.5
    if pair_potential:
        strength = 0.7
    if flush_potential > 0.6:
        strength = max(strength, 0.6)
    if high_card_strength > 0.8:
        strength = max(strength, 0.65)
    
    # Add some randomness for bluffing
    strength += random.uniform(-0.05, 0.05)
    return max(0.05, min(0.95, strength))

def pot_odds(state):
    """Return pot odds as a fraction."""
    to_call = state['to_call']
    pot_after_call = state['pot'] + to_call
    if to_call == 0:
        return 1.0
    return to_call / pot_after_call

def should_bluff(state, hand_strength):
    """Decide if we should bluff based on board texture and opponent action."""
    # Bluff if opponent seems weak (small bet) and we have little showdown value
    if hand_strength < 0.4 and state['to_call'] < state['pot'] * 0.3:
        # Occasionally bluff
        return random.random() < 0.3
    return False

def policy(state):
    # Legal actions
    legal = state['allowed_actions']
    
    # Estimate hand strength
    hand_strength = estimate_hand_strength(
        state['private_cards'],
        state['public_cards']
    )
    
    # Pot odds
    odds = pot_odds(state)
    
    # Effective odds needed
    needed_equity = odds + 0.05  # add small margin
    
    # Decision logic
    if hand_strength > 0.8 and 'raise' in legal:
        return 'raise'
    if hand_strength > 0.65 and 'raise' in legal and random.random() < 0.6:
        return 'raise'
    
    # Bluff opportunity
    if should_bluff(state, hand_strength) and 'raise' in legal:
        return 'raise'
    
    # Call or check
    if hand_strength > needed_equity:
        if 'call' in legal:
            return 'call'
    
    # Fold weak hands facing large bets
    if hand_strength < needed_equity * 0.7 and 'fold' in legal:
        return 'fold'
    
    # Default: call/check if possible, otherwise fold
    if 'call' in legal:
        return 'call'
    if 'fold' in legal:
        return 'fold'
    
    # Fallback (should not happen)
    return legal[0]
