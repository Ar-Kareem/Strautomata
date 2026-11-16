
import math

def policy(state: dict) -> str:
    # Preflop hand strength lookup (simplified)
    def get_preflop_strength(cards):
        if len(cards) != 2:
            return 0  # Shouldn't happen per problem statement

        rank1, rank2 = sorted([cards[0]['rank'], cards[1]['rank']], reverse=True)
        if rank1 == 14 and rank2 == 13: return 9  # AA
        if rank1 == 14 and rank2 >= 12: return 8  # AK, AQ
        if rank1 == 13 and rank2 >= 12: return 7  # KK, KQ
        if rank1 == 12 and rank2 >= 11: return 6  # QQ, QJ
        if rank1 == 11 and rank2 >= 10: return 5  # JJ, JT
        if rank1 == 10 and rank2 >= 9: return 4  # TT, T9
        if rank1 >= 9 and rank2 >= 8: return 3  # 99, 98, 88
        if rank1 >= 8 and rank2 >= 7: return 2  # 87, 77
        return 1  # Weak hands (e.g., 76, 65)

    # Postflop hand strength heuristic (simplified)
    def get_postflop_strength(private_cards, public_cards):
        # Count pairs, flushes, straights, etc.
        ranks = [c['rank'] for c in private_cards + public_cards]
        suits = [c['suit'] for c in private_cards + public_cards]

        # Pair strength
        pair_rank = max(set(ranks), key=ranks.count)
        pair_count = ranks.count(pair_rank)
        if pair_count >= 2:
            return 5 + (pair_rank // 2)  # Higher pair = stronger

        # Flush potential
        flush_suit = max(set(suits), key=suits.count)
        if suits.count(flush_suit) >= 4:
            return 4  # Nut flush

        # Straight potential
        unique_ranks = sorted(set(ranks))
        if len(unique_ranks) >= 5:
            for i in range(len(unique_ranks) - 4):
                if unique_ranks[i+4] - unique_ranks[i] == 4:
                    return 3  # Straight

        # High card
        return 1 + (max(ranks) // 3)  # Higher card = slightly stronger

    # Determine if we're preflop or postflop
    is_preflop = len(state['public_cards']) == 0
    hand_strength = get_preflop_strength(state['private_cards']) if is_preflop else get_postflop_strength(state['private_cards'], state['public_cards'])

    # Stack sizes (assuming 100 chips starting stack)
    my_stack = 100 - state['my_spent']
    opponent_stack = 100 - state['opponent_spent']
    pot = state['pot']
    to_call = state['to_call']

    # Pot odds
    pot_odds = (pot + to_call) / to_call if to_call > 0 else float('inf')

    # Aggression factor (higher = more aggressive)
    aggression = 1.0
    if is_preflop:
        aggression = 1.5 if hand_strength >= 5 else 0.5  # Aggressive with strong hands
    else:
        aggression = 1.2 if hand_strength >= 3 else 0.7  # Moderate postflop

    # Decide action
    if 'fold' in state['allowed_actions']:
        # Fold weak hands
        if hand_strength < 2 and to_call > 0:
            return 'fold'

    if 'all-in' in state['allowed_actions']:
        # All-in with premium hands when facing large bets
        if hand_strength >= 7 and to_call > 0 and to_call > my_stack * 0.5:
            return 'all-in'

    if 'raise' in state['allowed_actions']:
        # Raise with strong hands or strong draws
        if (hand_strength >= 5 and is_preflop) or (hand_strength >= 3 and not is_preflop):
            return 'raise'

    if 'call' in state['allowed_actions']:
        # Call if pot odds justify it
        if to_call == 0 or (hand_strength >= 2 and pot_odds >= 2.0):
            return 'call'

    # Default to call if no other action is better
    return 'call'
