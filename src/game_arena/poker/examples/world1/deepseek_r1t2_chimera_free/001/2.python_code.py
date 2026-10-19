
import random

def evaluate_hand(cards):
    """Evaluates hand strength. Higher scores mean stronger hands."""
    if len(cards) == 1:
        return cards[0]['rank']  # Pre-flop: hole card rank
    
    # Calculate ranks, suits, and counts
    ranks = sorted([c['rank'] for c in cards], reverse=True)
    suits = [c['suit'] for c in cards]
    
    # Check for pairs, three-of-a-kind, etc.
    rank_counts = {}
    for r in ranks:
        rank_counts[r] = rank_counts.get(r, 0) + 1
    max_rank_count = max(rank_counts.values())
    pair_count = len([c for c in rank_counts.values() if c == 2])
    
    # Hand strength classification
    if max_rank_count == 4:  # Four of a kind
        return 700 + max(ranks)
    elif max_rank_count == 3:
        if 2 in rank_counts.values():  # Full house
            return 600 + max(ranks)
        else:  # Three of a kind
            return 300 + max(ranks)
    elif pair_count >= 2:  # Two pair
        return 250 + max(ranks)
    elif max_rank_count == 2:  # One pair
        return 200 + max(ranks)
    
    # Flush check (ignore for <3 cards)
    if len(cards) >= 3:
        suit_counts = {}
        for s in suits:
            suit_counts[s] = suit_counts.get(s, 0) + 1
        if max(suit_counts.values()) >= 3:
            return 400  # Flush potential
    
    # Straight check
    unique_ranks = sorted(list(set(ranks)), reverse=True)
    straight = False
    for i in range(len(unique_ranks) - 4):
        if unique_ranks[i] - unique_ranks[i+4] == 4:
            straight = True
            break
    if straight:
        return 350 + unique_ranks[0]
    
    return max(ranks)  # High card

def policy(state: dict) -> str:
    my_card = state['private_cards'][0]
    public_cards = state['public_cards']
    all_cards = public_cards + [my_card]
    
    # Strength evaluation
    is_pre_flop = len(public_cards) == 0
    if is_pre_flop:
        strength = my_card['rank']
    else:
        strength = evaluate_hand(all_cards)
    
    # Dynamic thresholds
    high_threshold = 10 if is_pre_flop else 300
    med_threshold = 7 if is_pre_flop else 200
    
    # Pot odds calculation
    to_call = state['to_call']
    pot = state['pot']
    total_pot_after_call = pot + to_call * 2  # Opponent's existing bet + your call
    pot_odds = to_call / total_pot_after_call if total_pot_after_call > 0 else 0
    
    # Opponent aggression
    opp_aggression = state['opponent_spent'] / max(state['my_spent'], 1)
    allowed_actions = state['allowed_actions']
    
    # Core decision logic
    if strength >= high_threshold:  # Strong hands
        if 'all-in' in allowed_actions:
            return 'all-in'
        elif 'raise' in allowed_actions:
            return 'raise'
        else:
            return 'call' if 'call' in allowed_actions else 'fold'
    
    elif strength >= med_threshold:  # Medium hands
        if (pot_odds <= 0.4 or opp_aggression < 2) and 'call' in allowed_actions:
            if 'raise' in allowed_actions and opp_aggression < 1.5:
                return 'raise'
            else:
                return 'call'
        else:
            return 'call' if 'call' in allowed_actions else ('fold' if 'fold' in allowed_actions else 'raise')
    
    else:  # Weak hands
        if pot_odds <= 0.25 and 'call' in allowed_actions:
            return 'call'
        # Random bluff (10% chance) when raise allowed
        elif 'raise' in allowed_actions and random.random() < 0.1:
            return 'raise'
        else:
            return 'fold' if 'fold' in allowed_actions else 'call'
