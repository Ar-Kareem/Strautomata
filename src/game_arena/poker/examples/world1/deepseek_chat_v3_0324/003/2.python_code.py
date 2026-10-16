
import numpy as np
from collections import defaultdict

def policy(state: dict) -> str:
    # Extract game state information
    private_card = state['private_cards'][0]
    public_cards = state['public_cards']
    pot = state['pot']
    my_spent = state['my_spent']
    opponent_spent = state['opponent_spent']
    to_call = state['to_call']
    allowed_actions = state['allowed_actions']
    
    # Calculate hand strength
    hand_strength = evaluate_hand_strength(private_card, public_cards)
    
    # Calculate pot odds
    pot_odds = to_call / (pot + to_call) if to_call > 0 else 0
    
    # Determine aggression factor based on opponent's betting
    aggression_factor = calculate_aggression_factor(state)
    
    # Decision making
    if 'fold' in allowed_actions and should_fold(hand_strength, pot_odds, aggression_factor):
        return 'fold'
    
    if 'all-in' in allowed_actions and should_all_in(hand_strength, aggression_factor):
        return 'all-in'
    
    if 'raise' in allowed_actions and should_raise(hand_strength, aggression_factor):
        return 'raise'
    
    # Default to call/check
    return 'call'

def evaluate_hand_strength(private_card, public_cards):
    """Evaluate hand strength based on current cards"""
    rank = private_card['rank']
    suit = private_card['suit']
    
    # Pre-flop evaluation
    if not public_cards:
        # High cards are strong
        if rank >= 10:  # 10, J, Q, K, A
            return 0.7 + (rank - 10) * 0.08
        # Medium pairs are decent
        if rank >= 7:
            return 0.5
        # Low cards are weak
        return 0.2 + rank * 0.05
    
    # Post-flop evaluation
    ranks = [c['rank'] for c in public_cards] + [rank]
    suits = [c['suit'] for c in public_cards] + [suit]
    
    # Count pairs and suits
    rank_counts = defaultdict(int)
    suit_counts = defaultdict(int)
    for r in ranks:
        rank_counts[r] += 1
    for s in suits:
        suit_counts[s] += 1
    
    # Evaluate hand strength
    max_count = max(rank_counts.values())
    if max_count >= 4:
        return 1.0  # Quads
    if max_count == 3 and len([v for v in rank_counts.values() if v >= 2]) >= 2:
        return 0.95  # Full house
    if max(suit_counts.values()) >= 4:
        return 0.9  # Flush
    if len(public_cards) >= 3 and is_straight(ranks):
        return 0.85  # Straight
    if max_count == 3:
        return 0.7  # Three of a kind
    if len([v for v in rank_counts.values() if v >= 2]) >= 2:
        return 0.6  # Two pair
    if max_count == 2:
        return 0.4  # One pair
    return 0.2  # High card

def is_straight(ranks):
    """Check if cards form a straight"""
    unique_ranks = sorted(list(set(ranks)))
    if len(unique_ranks) < 5:
        return False
    # Check for regular straight
    for i in range(len(unique_ranks) - 4):
        if unique_ranks[i+4] - unique_ranks[i] == 4:
            return True
    # Check for wheel (A-2-3-4-5)
    if set([14, 2, 3, 4, 5]).issubset(set(ranks)):
        return True
    return False

def calculate_aggression_factor(state):
    """Calculate opponent's aggression based on betting patterns"""
    opponent_spent = state['opponent_spent']
    my_spent = state['my_spent']
    pot = state['pot']
    
    if my_spent == 0:
        return 1.0  # No information yet
    
    # Basic aggression measure
    aggression = opponent_spent / (my_spent + 0.01)
    return min(max(aggression, 0.5), 2.0)  # Clamp between 0.5 and 2.0

def should_fold(hand_strength, pot_odds, aggression_factor):
    """Determine if folding is the correct play"""
    # Never fold if it's free to check
    if pot_odds == 0:
        return False
    
    # Fold weak hands when pot odds are unfavorable
    if hand_strength < pot_odds * aggression_factor:
        return True
    
    return False

def should_all_in(hand_strength, aggression_factor):
    """Determine if going all-in is correct"""
    # Go all-in with very strong hands
    if hand_strength > 0.9:
        return True
    
    # Bluff occasionally with medium strength
    if hand_strength > 0.5 and np.random.random() < 0.1 * aggression_factor:
        return True
    
    return False

def should_raise(hand_strength, aggression_factor):
    """Determine if raising is correct"""
    # Raise with strong hands
    if hand_strength > 0.7:
        return True
    
    # Semi-bluff with decent hands
    if hand_strength > 0.4 and np.random.random() < 0.3 * aggression_factor:
        return True
    
    return False
