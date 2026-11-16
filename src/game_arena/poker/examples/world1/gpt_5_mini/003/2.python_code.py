
import random
import itertools
from typing import List, Dict, Tuple

# Poker hand categories (higher is better)
# 8: Straight flush
# 7: Four of a kind
# 6: Full house
# 5: Flush
# 4: Straight
# 3: Three of a kind
# 2: Two pair
# 1: One pair
# 0: High card

def card_key(c: Dict) -> Tuple[int, int]:
    return (c['rank'], c['suit'])

def five_card_score(cards: List[Dict]) -> Tuple[int, List[int]]:
    # cards: list of 5 card dicts
    ranks = [c['rank'] for c in cards]
    suits = [c['suit'] for c in cards]
    # Sort ranks descending
    ranks_sorted = sorted(ranks, reverse=True)
    # Count ranks
    counts = {}
    for r in ranks:
        counts[r] = counts.get(r, 0) + 1
    # For later kicker ordering
    # Prepare list of (count, rank) sorted by count desc then rank desc
    count_rank = sorted(((cnt, r) for r, cnt in counts.items()), reverse=True)
    # Flush?
    flush = max([suits.count(s) for s in set(suits)]) == 5
    # Straight?
    uniq = sorted(set(ranks))
    # Handle Ace-low straight: map Ace(14) to 1 as well
    straight_high = None
    rset = set(uniq)
    if len(rset) >= 5:
        # For 5-card hand, check simple consecutive condition
        sorted_uniq = sorted(rset)
        # Check normal straight (highest possible)
        for i in range(len(sorted_uniq)-4):
            if (sorted_uniq[i+4] - sorted_uniq[i]) == 4 and \
               sorted_uniq[i+1] == sorted_uniq[i]+1 and \
               sorted_uniq[i+2] == sorted_uniq[i]+2 and \
               sorted_uniq[i+3] == sorted_uniq[i]+3:
                straight_high = sorted_uniq[i+4]
        # Check wheel A-2-3-4-5
        if not straight_high:
            if set([14, 2, 3, 4, 5]).issubset(rset):
                straight_high = 5
    # Straight flush?
    if flush:
        # Filter by suit
        suit = cards[0]['suit']
        # But suits may be different; find correct suit with 5 cards
        suit_counts = {}
        for c in cards:
            suit_counts.setdefault(c['suit'], []).append(c)
        for s, clist in suit_counts.items():
            if len(clist) >= 5:
                # Collect ranks of that suit and check straight
                sranks = sorted(set([c['rank'] for c in clist]))
                sf_high = None
                if len(sranks) >= 5:
                    for i in range(len(sranks)-4):
                        if (sranks[i+4] - sranks[i]) == 4 and \
                           sranks[i+1] == sranks[i]+1 and \
                           sranks[i+2] == sranks[i]+2 and \
                           sranks[i+3] == sranks[i]+3:
                            sf_high = sranks[i+4]
                    if not sf_high:
                        if set([14, 2, 3, 4, 5]).issubset(sranks):
                            sf_high = 5
                if sf_high:
                    return (8, [sf_high])
    # Four of a kind
    if 4 in counts.values():
        quad_rank = max(r for r, cnt in counts.items() if cnt == 4)
        kicker = max(r for r in ranks if r != quad_rank)
        return (7, [quad_rank, kicker])
    # Full house
    trips = [r for r, cnt in counts.items() if cnt == 3]
    pairs = [r for r, cnt in counts.items() if cnt == 2]
    if trips:
        # If multiple trips, one act as trips, other as pair
        if len(trips) >= 2:
            top_trips = sorted(trips, reverse=True)
            return (6, [top_trips[0], top_trips[1]])
        if pairs:
            return (6, [max(trips), max(pairs)])
    # Flush
    if flush:
        # choose top 5 ranks of the flush suit
        suit_counts = {}
        for c in cards:
            suit_counts.setdefault(c['suit'], []).append(c['rank'])
        for s, rl in suit_counts.items():
            if len(rl) >= 5:
                top5 = sorted(rl, reverse=True)[:5]
                return (5, top5)
    # Straight
    if straight_high:
        return (4, [straight_high])
    # Three of a kind
    if 3 in counts.values():
        trip_rank = max(r for r, cnt in counts.items() if cnt == 3)
        kickers = sorted([r for r in ranks if r != trip_rank], reverse=True)[:2]
        return (3, [trip_rank] + kickers)
    # Two pair
    pair_ranks = sorted([r for r, cnt in counts.items() if cnt == 2], reverse=True)
    if len(pair_ranks) >= 2:
        top2 = pair_ranks[:2]
        kicker = max(r for r in ranks if r not in top2)
        return (2, top2 + [kicker])
    # One pair
    if len(pair_ranks) == 1:
        pr = pair_ranks[0]
        kickers = sorted([r for r in ranks if r != pr], reverse=True)[:3]
        return (1, [pr] + kickers)
    # High card
    return (0, sorted(ranks, reverse=True)[:5])

def best_hand(cards: List[Dict]) -> Tuple[int, List[int]]:
    # Choose best 5-card hand from up to 7 cards
    best = (-1, [])
    for comb in itertools.combinations(cards, 5):
        sc = five_card_score(list(comb))
        if sc > best:
            best = sc
    return best

def compare_hands(a: Tuple[int, List[int]], b: Tuple[int, List[int]]) -> int:
    # return 1 if a>b, 0 tie, -1 if a<b
    if a[0] != b[0]:
        return 1 if a[0] > b[0] else -1
    # compare tiebreakers lexicographically
    for x, y in zip(a[1], b[1]):
        if x != y:
            return 1 if x > y else -1
    return 0

def make_deck() -> List[Dict]:
    deck = []
    for r in range(2, 15):  # 2..14 (Ace=14)
        for s in range(4):
            deck.append({'rank': r, 'suit': s})
    return deck

def card_equal(a: Dict, b: Dict) -> bool:
    return a['rank'] == b['rank'] and a['suit'] == b['suit']

def remove_known(deck: List[Dict], known: List[Dict]) -> List[Dict]:
    remaining = []
    for c in deck:
        skip = False
        for k in known:
            if card_equal(c, k):
                skip = True
                break
        if not skip:
            remaining.append(c)
    return remaining

def estimate_equity_approx(my_card: Dict, public_cards: List[Dict], samples: int = 300) -> float:
    # Monte Carlo sampling: sample opponent one-card and remaining public cards
    deck = make_deck()
    known = [my_card] + public_cards
    deck = remove_known(deck, known)
    n_public = len(public_cards)
    need = 5 - n_public
    wins = 0
    ties = 0
    losses = 0
    if need < 0:
        need = 0
    # If there are no unknowns (board complete), we can iterate all opponent possibilities
    if need == 0:
        for opp in deck:
            my_cards = [my_card] + public_cards
            opp_cards = [opp] + public_cards
            my_best = best_hand(my_cards)
            opp_best = best_hand(opp_cards)
            cmp = compare_hands(my_best, opp_best)
            if cmp > 0:
                wins += 1
            elif cmp == 0:
                ties += 1
            else:
                losses += 1
        total = wins + ties + losses
        if total == 0:
            return 0.5
        return (wins + ties * 0.5) / total
    # Otherwise sample
    deck_list = deck[:]  # remaining cards
    # Reduce samples if deck small
    samples = min(samples, max(50, len(deck_list) * 3))
    for _ in range(samples):
        # shuffle and pick
        if len(deck_list) < need + 1:
            break
        picks = random.sample(deck_list, need + 1)  # first is opponent card, rest are remaining board
        opp = picks[0]
        board_add = picks[1:]
        board = public_cards + board_add
        my_cards = [my_card] + board
        opp_cards = [opp] + board
        my_best = best_hand(my_cards)
        opp_best = best_hand(opp_cards)
        cmp = compare_hands(my_best, opp_best)
        if cmp > 0:
            wins += 1
        elif cmp == 0:
            ties += 1
        else:
            losses += 1
    total = wins + ties + losses
    if total == 0:
        return 0.5
    return (wins + ties * 0.5) / total

def legal_action_choice(preferred: List[str], allowed: List[str], fallback_order: List[str]) -> str:
    for a in preferred:
        if a in allowed:
            return a
    for a in fallback_order:
        if a in allowed:
            return a
    # As last resort, return any allowed action
    return allowed[0]

def policy(state: dict) -> str:
    """
    Return one of: 'fold', 'call', 'raise', 'all-in'
    """
    allowed = state.get('allowed_actions', [])
    # Defensive: must return a legal action
    if not allowed:
        return 'call'

    my_card = state['private_cards'][0]
    public = state.get('public_cards', [])
    pot = state.get('pot', 0)
    to_call = state.get('to_call', 0)
    my_spent = state.get('my_spent', 0)
    opp_spent = state.get('opponent_spent', 0)

    # Do not allow folding in the very first round when both players only have 100 in the pot.
    # Heuristic: if pot==100 and both spent equal and to_call==0, disallow folding.
    forbid_fold = False
    if 'fold' in allowed and pot == 100 and my_spent == opp_spent and to_call == 0:
        forbid_fold = True

    # Estimate equity via Monte Carlo
    # If public cards are complete, estimator is exact (iterating opponent cards).
    # Use more samples when few public cards known.
    n_public = len(public)
    if n_public == 5:
        samples = 0
    elif n_public >= 3:
        samples = 200
    elif n_public == 0:
        samples = 400
    else:
        samples = 300

    equity = estimate_equity_approx(my_card, public, samples=samples)

    # Pot odds when facing a bet
    if to_call > 0:
        pot_odds = to_call / (pot + to_call)  # break-even equity needed to call
    else:
        pot_odds = 0.0

    # Basic thresholds tuned for single-card hold'em
    # Aggression when equity high, call when equity beats pot odds, else fold (if allowed)
    # If to_call == 0: check (call) unless strong enough to raise.
    action = None

    # Super strong -> shove
    if equity >= 0.90 and 'all-in' in allowed:
        action = 'all-in'
    elif equity >= 0.80:
        # Strong: raise if allowed, else all-in if permitted, else call/check
        if 'raise' in allowed:
            action = 'raise'
        elif 'all-in' in allowed:
            action = 'all-in'
        else:
            action = 'call' if 'call' in allowed else ( 'fold' if 'fold' in allowed and not forbid_fold else allowed[0] )
    else:
        # Moderate cases
        if to_call == 0:
            # No cost to continue: check (call) unless we are strong enough to bet
            if equity >= 0.55 and 'raise' in allowed:
                action = 'raise'
            elif equity >= 0.65 and 'all-in' in allowed:
                action = 'all-in'
            else:
                # prefer 'call' as check
                if 'call' in allowed:
                    action = 'call'
                elif 'raise' in allowed:
                    action = 'raise'
                elif 'all-in' in allowed:
                    action = 'all-in'
                else:
                    action = allowed[0]
        else:
            # Facing a bet: compare equity to pot odds with margin
            margin = 0.02  # risk margin
            if equity + 1e-9 >= pot_odds - 1e-12:
                # calling is at least break-even
                # If significantly ahead of odds, raise
                if equity >= max(pot_odds + 0.20, 0.60) and 'raise' in allowed:
                    action = 'raise'
                elif equity >= 0.70 and 'all-in' in allowed:
                    action = 'all-in'
                else:
                    if 'call' in allowed:
                        action = 'call'
                    elif 'all-in' in allowed and equity > pot_odds:
                        action = 'all-in'
                    elif 'fold' in allowed and not forbid_fold:
                        action = 'fold'
                    else:
                        # fallback
                        action = legal_action_choice(['call', 'fold', 'all-in', 'raise'], allowed, ['call', 'fold', 'all-in', 'raise'])
            else:
                # Not good enough to call
                # Occasionally bluff: small chance to raise if allowed and board thin
                # But keep it modest
                bluff_chance = 0.02
                board_texture = len(public)
                # More likely to bluff on heads-up preflop or dry boards
                if 'raise' in allowed and random.random() < bluff_chance and board_texture <= 3:
                    action = 'raise'
                else:
                    # Fold if allowed
                    if 'fold' in allowed and not forbid_fold:
                        action = 'fold'
                    elif 'call' in allowed:
                        action = 'call'
                    elif 'all-in' in allowed and equity > pot_odds:
                        action = 'all-in'
                    else:
                        action = allowed[0]

    # Ensure returned action is legal and obeys fold prohibition
    if action not in allowed or (action == 'fold' and forbid_fold):
        # Try fallbacks
        if 'call' in allowed:
            if not (state.get('to_call', 0) == 0 and 'call' in allowed):
                # okay to call
                action = 'call'
            else:
                action = 'call'
        elif 'raise' in allowed:
            action = 'raise'
        elif 'all-in' in allowed:
            action = 'all-in'
        else:
            # last resort
            for a in allowed:
                if a != 'fold' or not forbid_fold:
                    action = a
                    break
            if action is None:
                action = allowed[0]

    return action
