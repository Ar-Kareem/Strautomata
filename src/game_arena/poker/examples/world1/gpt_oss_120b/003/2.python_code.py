
import random
import itertools
from typing import List, Dict, Tuple

# ----- Poker hand evaluator (5‑card) -----
RANK_ORDER = list(range(2, 15))  # 2‑14 (Ace high)

def _group_by_rank(cards: List[Dict]) -> Tuple[List[int], List[int]]:
    """Return (sorted ranks by count then rank, list of suits)."""
    rank_counts = {}
    suits = []
    for c in cards:
        r = c['rank']
        rank_counts[r] = rank_counts.get(r, 0) + 1
        suits.append(c['suit'])
    # sort by count descending, then rank descending
    sorted_ranks = sorted(rank_counts.items(),
                          key=lambda x: (x[1], x[0]),
                          reverse=True)
    ranks_by_cnt = [r for r, cnt in sorted_ranks for _ in range(cnt)]
    return ranks_by_cnt, suits

def _is_straight(ranks: List[int]) -> Tuple[bool, int]:
    """Detect straight, return (is_straight, high_card). Handles wheel A‑2‑3‑4‑5."""
    uniq = sorted(set(ranks))
    if len(uniq) < 5:
        return False, 0
    # normal straight
    for i in range(len(uniq) - 4):
        window = uniq[i:i+5]
        if window[4] - window[0] == 4:
            return True, window[4]
    # wheel straight (A‑2‑3‑4‑5)
    if set([14, 2, 3, 4, 5]).issubset(set(uniq)):
        return True, 5
    return False, 0

def hand_rank(cards: List[Dict]) -> Tuple[int, List[int]]:
    """Return a tuple that can be compared directly. Higher is better."""
    # cards length may be >5; caller should choose best 5‑card combination.
    ranks = [c['rank'] for c in cards]
    suits = [c['suit'] for c in cards]

    # flush detection
    suit_counts = {}
    for s in suits:
        suit_counts[s] = suit_counts.get(s, 0) + 1
    flush_suit = None
    for s, cnt in suit_counts.items():
        if cnt >= 5:
            flush_suit = s
            break

    # straight detection
    is_straight, straight_high = _is_straight(ranks)

    # straight flush / royal
    if flush_suit is not None:
        flush_cards = [c for c in cards if c['suit'] == flush_suit]
        f_ranks = [c['rank'] for c in flush_cards]
        is_sf, sf_high = _is_straight(f_ranks)
        if is_sf:
            # royal flush is just highest straight flush
            return (9, [sf_high])  # straight flush
    # Four of a kind
    rank_counts = {}
    for r in ranks:
        rank_counts[r] = rank_counts.get(r, 0) + 1
    fours = [r for r, cnt in rank_counts.items() if cnt == 4]
    if fours:
        kicker = max([r for r in ranks if r not in fours])
        return (8, [fours[0], kicker])
    # Full house
    threes = [r for r, cnt in rank_counts.items() if cnt == 3]
    pairs = [r for r, cnt in rank_counts.items() if cnt == 2]
    if threes:
        if pairs:
            return (7, [max(threes), max(pairs)])
        # possible double three‑of‑a‑kind, use second three as pair
        if len(threes) >= 2:
            threes_sorted = sorted(threes, reverse=True)
            return (7, [threes_sorted[0], threes_sorted[1]])
    # Flush
    if flush_suit is not None:
        flush_r = sorted([c['rank'] for c in cards if c['suit'] == flush_suit],
                         reverse=True)[:5]
        return (6, flush_r)
    # Straight
    if is_straight:
        return (5, [straight_high])
    # Three of a kind
    if threes:
        kicker = sorted([r for r in ranks if r != threes[0]], reverse=True)[:2]
        return (4, [threes[0]] + kicker)
    # Two pair
    if len(pairs) >= 2:
        top_two = sorted(pairs, reverse=True)[:2]
        kicker = max([r for r in ranks if r not in top_two])
        return (3, top_two + [kicker])
    # One pair
    if pairs:
        kicker = sorted([r for r in ranks if r != pairs[0]], reverse=True)[:3]
        return (2, [pairs[0]] + kicker)
    # High card
    high = sorted(ranks, reverse=True)[:5]
    return (1, high)

def best_five_rank(all_cards: List[Dict]) -> Tuple[int, List[int]]:
    """Choose best 5‑card hand from up to 7 cards."""
    if len(all_cards) == 5:
        return hand_rank(all_cards)
    best = (0, [])
    for combo in itertools.combinations(all_cards, 5):
        cur = hand_rank(list(combo))
        if cur > best:
            best = cur
    return best

# ----- Monte‑Carlo equity estimator -----
def estimate_equity(state: Dict, sims: int = 800) -> float:
    """Return win probability (0‑1) of my hand against a random opponent."""
    my_cards = state['private_cards']
    board = state['public_cards']
    known = my_cards + board

    # Build full deck
    deck = [{'rank': r, 'suit': s} for r in RANK_ORDER for s in range(4)]
    # remove known cards
    def card_eq(a, b):
        return a['rank'] == b['rank'] and a['suit'] == b['suit']
    remaining = [c for c in deck if not any(card_eq(c, k) for k in known)]

    wins = 0
    ties = 0
    needed_board = 5 - len(board)

    for _ in range(sims):
        # sample opponent private card
        opp_private = random.choice(remaining)
        # sample missing board cards
        pool = [c for c in remaining if not card_eq(c, opp_private)]
        board_draw = random.sample(pool, needed_board) if needed_board > 0 else []
        full_board = board + board_draw

        # evaluate my hand
        my_best = best_five_rank(my_cards + full_board)
        opp_best = best_five_rank([opp_private] + full_board)

        if my_best > opp_best:
            wins += 1
        elif my_best == opp_best:
            ties += 1
        # else loss

    total = sims
    return (wins + ties * 0.5) / total

# ----- Main policy function -----
def policy(state: Dict) -> str:
    """
    Decide the next action in a heads‑up Hold'em game.
    Returns one of: 'fold', 'call', 'raise', 'all-in'.
    """
    # quick sanity: if no legal actions, default to fold
    actions = state.get('allowed_actions', [])
    if not actions:
        return 'fold'

    to_call = state.get('to_call', 0)
    pot = state.get('pot', 0)

    # Estimate hand equity
    equity = estimate_equity(state, sims=800)

    # Pot odds (fraction of total pot we must invest)
    pot_odds = 0.0
    if to_call > 0:
        pot_odds = to_call / (pot + to_call)

    # --- Decision rules ---
    # 1. Free check situation
    if to_call == 0:
        # If we have a strong hand, try to raise
        if 'raise' in actions and equity > 0.65:
            return 'raise'
        # otherwise just check (call)
        return 'call'  # check

    # 2. When we must put chips in
    # Prefer folding only if clearly disadvantageous and folding is allowed
    # but not when pot is zero (initial hand) as per rule.
    if equity > pot_odds + 0.08:
        # Good enough to call – maybe raise if very strong
        if 'raise' in actions and equity > 0.75:
            return 'raise'
        if 'call' in actions:
            return 'call'
    else:
        # Equity low – fold if possible
        if 'fold' in actions and state.get('pot', 0) > 0:
            return 'fold'

    # 3. Fallback – choose the most aggressive allowed action when equity is high,
    # otherwise call.
    if equity > 0.8 and 'all-in' in actions:
        return 'all-in'
    if 'call' in actions:
        return 'call'
    if 'raise' in actions:
        return 'raise'
    # Last resort
    return actions[0]

