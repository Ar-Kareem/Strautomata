
import itertools
from collections import defaultdict

def evaluate_hand(cards):
    # This function evaluates a 5-card hand and returns a tuple (hand_type, kicker_values)
    # The hand_type is such that lower values indicate stronger hands (0 = strongest, 8 = weakest)
    ranks = [card['rank'] for card in cards]
    suits = [card['suit'] for card in cards]
    unique_ranks = sorted(list(set(ranks)), reverse=True)
    rank_counts = defaultdict(int)
    for r in ranks:
        rank_counts[r] += 1
    sorted_reranks = sorted(rank_counts.items(), key=lambda x: (-x[1], -x[0]))

    def is_straight(rlist):
        l = list(set(rlist))
        l.sort(reverse=True)
        for i in range(len(l) - 4):
            if all(l[i] == l[i + j] + j for j in range(1, 5)):
                return s_rank(l[i])
        for i in [0, 5, 4, 3, 2]:
            if i in unique_ranks and 14 in unique_ranks and i + 3 in unique_ranks:
                return 5
        return False

    is_flush = (len(suits) == 1)
    if flush:
        straight = is_straight(ranks)
        if straight:
            best_rank = 0
            kicker = sorted([c['rank'] for c in cards], reverse=True)
            if kicker[0] == 14:
                kicker[0] = 1
            return (best_rank, kicker[::-1])
        else:
            return (3, sorted(rank_counts.keys(), reverse=True))
    sorted_ranks = sorted(ranks, reverse=True)
    seq = []
    last = None
    for r in sorted_ranks:
        if len(seq) == 0 or r == last - 1:
            seq.append(r)
            last = r
        else:
            if len(seq) > 0 and r + 1 == seq[0]:
                seq = [r] + seq
                last = r
            seq = [r]
    if len(seq) >= 5:
        return (4, seq[:5] + sorted([r for r in ranks if r not in seq], reverse=True))
    counts = []
    suits_cnt = defaultdict(int)
    for s in suits:
        suits_cnt[s] += 1
    suit_order = sorted(suits_cnt.values(), reverse=True)
    for key in sorted(rank_counts.keys()):
        counts.append(rank_counts[key])
    counts_sorted = sorted(counts, reverse=True)
    if counts_sorted[0] == 5:
        return (0, ranks)
    if flush:
        return (3, ranks)
    if counts_sorted[0] == 4:
        quad_rank = max(r for r, count in rank_counts.items() if count == 4)
        kicker = max(r for r, count in rank_counts.items() if count == 1)
        return (1, [quad_rank, kicker])
    if counts_sorted[0] == 3 and counts_sorted[1] == 2:
        return (2, [max(r for r, count in sorted_reranks.items() if count == 3), 
                    max(r for r, count in rank_counts.items() if count == 2)])
    if counts_sorted[0] == 3:
        three_rank = max(r for r, count in rank_counts.items() if count == 3)
        other_ranks = sorted([r for r in rank_counts if rank_counts[r] != 3] + [r for r, count in rank_counts.items() if count == 3], reverse=True)
        return (5, [three_rank, other_ranks[0], other_ranks[1]])
    if len(counts_sorted) >= 2 and counts_sorted[0] == 2 and counts_sorted[1] == 2:
        pair_ranks = sorted([r for r, count in rank_counts.items() if count == 2], reverse=True)
        kicker = max(r for r, count in rank_counts.items() if count == 1)
        return (6, pair_ranks + [kicker])
    if counts_sorted[0] == 2:
        pair_rank = max(r for r, count in rank_counts.items() if count == 2)
        kickers = sorted([r for r in rank_counts if rank_counts[r] != 2], reverse=True)[:3]
        return (7, [pair_rank] + kickers)
    return (9, sorted(ranks, reverse=True))

def policy(state):
    public = state['public_cards']
    private = state['private_cards']
    all_cards = private + public
    allowed_actions = state['allowed_actions']
    
    if len(all_cards) < 5:
        if 'fold' in allowed_actions and state['to_call'] > 0:
            return 'fold'
        else:
            return 'call' if 'call' in allowed_actions else 'raise'
    
    best_hand = None
    best_rank = (10,)
    for combo in itertools.combinations(all_cards, 5):
        score = evaluate_hand(list(combo))
        if score < best_rank:
            best_rank = score
            best_hand = combo
        elif score == best_rank and list(combo) > best_hand:
            best_hand = combo
    
    if best_rank[0] <= 3:
        return 'all-in' if 'all-in' in allowed_actions and state['my_spent'] <= (state['pot'] - state['to_call']) else 'raise'
    elif best_rank[0] <= 5:
        return 'raise' if 'raise' in allowed_actions else 'call' if 'call' in allowed_actions else 'fold'
    else:
        if state['to_call'] > 0 and 'call' in allowed_actions:
            return 'call'
        else:
            return 'fold'
