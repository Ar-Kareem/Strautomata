
import numpy as np
import random

def evaluate_hand_strength(private_cards, public_cards):
    """
    Simple evaluation of hand strength based on poker rules
    Returns a value between 0 and 1 indicating hand strength
    """
    # Combine hole cards and public cards
    all_cards = private_cards + public_cards
    
    # Count ranks and suits
    ranks = [card['rank'] for card in all_cards]
    suits = [card['suit'] for card in all_cards]
    
    rank_counts = {}
    for rank in ranks:
        rank_counts[rank] = rank_counts.get(rank, 0) + 1
    
    # Get rank frequencies
    rank_freq = list(rank_counts.values())
    rank_freq.sort(reverse=True)
    
    # Check for pairs, trips, quads
    has_pair = 2 in rank_freq
    has_two_pair = rank_freq.count(2) >= 2
    has_trips = 3 in rank_freq
    has_quads = 4 in rank_freq
    
    # Check for flush
    suit_counts = {}
    for suit in suits:
        suit_counts[suit] = suit_counts.get(suit, 0) + 1
    has_flush = max(suit_counts.values()) >= 5
    
    # Check for straight
    unique_ranks = sorted(list(set(ranks)))
    has_straight = False
    if len(unique_ranks) >= 5:
        # Simple straight check (doesn't account for ace-low straights)
        for i in range(len(unique_ranks) - 4):
            if unique_ranks[i+4] - unique_ranks[i] == 4:
                has_straight = True
                break
    
    # Hand strength values (higher is better)
    base_strength = 0
    
    # High card is better when no good combinations
    if not has_pair and not has_straight and not has_flush:
        # Just compare high card
        base_strength = max(ranks) / 14.0  # Normalize to [0,1]
    
    # Pair - stronger with higher rank
    if has_pair:
        pair_rank = max([rank for rank in ranks if ranks.count(rank) >= 2])
        base_strength = 0.2 + (pair_rank / 14.0) * 0.3
    
    # Two pair
    if has_two_pair:
        base_strength = 0.5 + (max([rank for rank in ranks if ranks.count(rank) >= 2]) / 14.0) * 0.3
    
    # Trips
    if has_trips:
        trips_rank = max([rank for rank in ranks if ranks.count(rank) >= 3])
        base_strength = 0.8 + (trips_rank / 14.0) * 0.2
    
    # Straight
    if has_straight:
        base_strength = 0.6
    
    # Flush
    if has_flush:
        base_strength = 0.7
    
    # Full house
    if has_trips and has_pair:
        base_strength = 0.9
    
    # Quad
    if has_quads:
        base_strength = 0.95
    
    # Royal flush (if applicable)
    # We don't calculate it since not relevant in this setting, but it would be highest
    
    return base_strength

def get_pot_odds(to_call, pot):
    """Calculate pot odds as a percentage"""
    if to_call == 0:
        return 100  # Pot odds infinite when no bet to call
    return 100 * (pot / (to_call + pot))

def policy(state: dict) -> str:
    # Extract the state fields
    private_cards = state['private_cards']
    public_cards = state['public_cards']
    pot = state['pot']
    my_spent = state['my_spent']
    opponent_spent = state['opponent_spent']
    to_call = state['to_call']
    allowed_actions = state['allowed_actions']
    
    # If only 100 in pot (first round) and can fold, assume we're allowed to fold even if only one action is available
    # But it's always fine if we have allowed actions including fold
    if pot == 0 and len(allowed_actions) > 1:
        pass  # Let's not fold in this initial situation
    
    # Evaluate our hand strength
    strength = evaluate_hand_strength(private_cards, public_cards)
    
    # Calculate pot odds
    pot_odds = get_pot_odds(to_call, pot)
    
    # Get current bet size
    current_bet = to_call
    
    # If we have a very strong hand and can afford to raise
    if strength > 0.85 and 'raise' in allowed_actions:
        return 'raise'
    
    # If we have a strong hand and no bet to match, check
    if strength > 0.6 and to_call == 0:
        if 'raise' in allowed_actions:
            return 'raise'  # Raise with good hand when no bet to call
        return 'call'  # At least call with decent hand when safe
    
    # If we have a decent hand and the pot odds are good
    if strength > 0.4 and pot_odds < 30 and to_call > 0:
        if 'call' in allowed_actions:
            return 'call'
    
    # If we have a bit of a hand and pot odds are attractive
    if strength > 0.3 and pot_odds < 50 and to_call > 0:
        if 'call' in allowed_actions:
            return 'call'
    
    # If we have a marginal hand, but we think our opponent might fold
    # Let's make the game interesting by calling with some marginal hands that are worth considering,
    # especially with suited connectors or medium cards
    cards_ranks = [card['rank'] for card in private_cards]
    pair_of_same_rank = len(set(cards_ranks)) <= 1
    
    # This is a very basic approach, actually, but it relies on remaining hand strength evaluation logic
    # So with exactly one card (a simplified model), we should perhaps just be smart about it.
    
    if strength > 0.4 and to_call > 0 and 'call' in allowed_actions:  
        # Moderate hands with reasonable pot odds can call
        return 'call'
    
    # If we have a very weak hand, fold
    if strength < 0.3 and to_call > 0:
        if 'fold' in allowed_actions:
            return 'fold'
    
    # If there's no cost to call, check or raise depending on strength
    if to_call == 0:
        # Check if we might want to raise with a good hand
        if strength > 0.5 and 'raise' in allowed_actions:
            return 'raise'
        else:
            return 'call'  # Safe move in no bet situation
    
    # Default fallback logic to make sure we have a valid move
    if 'call' in allowed_actions:
        return 'call'
    elif 'fold' in allowed_actions:
        return 'fold'
    elif 'raise' in allowed_actions:
        return 'raise'
    else:
        return 'all-in'

