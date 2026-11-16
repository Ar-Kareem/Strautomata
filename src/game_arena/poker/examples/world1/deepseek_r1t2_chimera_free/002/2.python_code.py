
import itertools
from collections import Counter

def evaluate_combo(cards):
    ranks = sorted([c['rank'] for c in cards], reverse=True)
    suits = [c['suit'] for c in cards]
    is_flush = len(set(suits)) == 1

    unique_ranks = sorted(set(ranks), reverse=True)
    is_straight = False
    high = 0
    for i in range(len(unique_ranks) - 4):
        if unique_ranks[i] - unique_ranks[i+4] == 4:
            is_straight = True
            high = unique_ranks[i]
            break
    if not is_straight and any(r in unique_ranks for r in [14, 2, 3, 4, 5]):
        if set([14, 2, 3, 4, 5]).issubset(unique_ranks):
            is_straight = True
            high = 5

    if is_straight and is_flush:
        return 8 + high / 14.0
    count = Counter(ranks)
    mc = count.most_common()
    if mc[0][1] == 4:
        kicker = next(r for r in ranks if r != mc[0][0])
        return 7 + mc[0][0] / 14.0 + kicker / 14.0 * 0.1
    elif mc[0][1] == 3 and len(mc) > 1 and mc[1][1] >= 2:
        return 6 + mc[0][0]/14.0 + mc[1][0]/14.0 * 0.1
    elif is_flush:
        flush_ranks = sorted(ranks, reverse=True)[:5]
        return 5 + sum(r / 14.0 for r in flush_ranks[:1]) / 5.0
    elif is_straight:
        return 4 + high / 14.0
    elif mc[0][1] == 3:
        return 3 + mc[0][0]/14.0 + sum(r for r in set(ranks) if r != mc[0][0])/(14.0 * (len(ranks)-1)) * 0.1
    elif len(mc) > 1 and mc[0][1] == 2 and mc[1][1] == 2:
        pairs = sorted([mc[0][0], mc[1][0]], reverse=True)
        kicker = next(r for r in ranks if r not in pairs)
        return 2 + pairs[0]/14.0 * 0.6 + pairs[1]/14.0 * 0.3 + kicker/14.0 * 0.1
    elif mc[0][1] == 2:
        return 1 + mc[0][0]/14.0 * 0.7 + sum(r for r in set(ranks) if r != mc[0][0])/(14.0 * (len(ranks)-1)) * 0.3
    else:
        return sum(ranks[:5]) / (14.0 * 5)

def evaluate_hand(p_cards, b_cards):
    all_cards = p_cards + b_cards
    n = len(all_cards)
    if n < 5:
        if not b_cards:
            return (p_cards[0]['rank'] / 14.0) * 0.6
        my_rank = p_cards[0]['rank']
        board_ranks = [c['rank'] for c in b_cards]
        if my_rank in board_ranks:
            return 0.5
        max_board = max(board_ranks) if board_ranks else 0
        return max(my_rank, max_board) / 14.0 * 0.8
    else:
        best_score = 0
        for combo in itertools.combinations(all_cards, 5):
            score = evaluate_combo(combo)
            best_score = max(best_score, score)
        return best_score / 9.0

def policy(state: dict) -> str:
    p_cards = state['private_cards']
    b_cards = state['public_cards']
    pot = state['pot']
    to_call = state['to_call']
    allowed = state['allowed_actions']

    strength = evaluate_hand(p_cards, b_cards)
    pot_total = pot + to_call
    pot_odds = to_call / pot_total if pot_total > 0 else 0

    if 'fold' in allowed and (strength < pot_odds - 0.1 or strength < 0.3):
        return 'fold'
    if strength > 0.8 and 'all-in' in allowed:
        return 'all-in'
    if strength > pot_odds + 0.15 and 'raise' in allowed:
        return 'raise'
    if 'call' in allowed:
        return 'call'
    return allowed[0]
