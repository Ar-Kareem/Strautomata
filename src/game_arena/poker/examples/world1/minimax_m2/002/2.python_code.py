
import random
from itertools import combinations
from collections import Counter

# ------------------------------------------------------------
# Card representation helpers
# ------------------------------------------------------------
RANKS = list(range(2, 15))      # 2 … Ace (14)
SUITS = list(range(4))

def card_to_tuple(card: dict) -> tuple:
    """Convert a card dict {'rank':..., 'suit':...} to (rank, suit)."""
    return (card['rank'], card['suit'])

def tuple_to_card(t: tuple) -> dict:
    return {'rank': t[0], 'suit': t[1]}

# ------------------------------------------------------------
# Hand evaluator (best 5‑card hand out of the given cards)
# ------------------------------------------------------------
def rank_hand(hand):
    """
    Return a comparable tuple that encodes the strength of a 5‑card hand.
    Higher tuple -> stronger hand.
    """
    # hand: list of 5 dicts {'rank':int, 'suit':int}
    ranks = [c['rank'] for c in hand]
    suits = [c['suit'] for c in hand]
    cnt = Counter(ranks)
    # Flush?
    is_flush = len(set(suits)) == 1
    # Straight?
    uniq = sorted(set(ranks))
    is_straight = False
    straight_high = None
    if len(uniq) == 5:
        # Normal straight
        if uniq[-1] - uniq[0] == 4:
            is_straight = True
            straight_high = uniq[-1]
        # Wheel (A‑2‑3‑4‑5)
        elif uniq == [2, 3, 4, 5, 14]:
            is_straight = True
            straight_high = 5

    # Straight flush
    if is_flush and is_straight:
        return (8, straight_high)
    # Four of a kind
    if 4 in cnt.values():
        quad_rank = next(r for r, c in cnt.items() if c == 4)
        kicker = next(r for r, c in cnt.items() if c == 1)
        return (7, quad_rank, kicker)
    # Full house
    if sorted(cnt.values(), reverse=True) == [3, 2]:
        triple = next(r for r, c in cnt.items() if c == 3)
        pair = next(r for r, c in cnt.items() if c == 2)
        return (6, triple, pair)
    # Flush
    if is_flush:
        return (5,) + tuple(sorted(ranks, reverse=True))
    # Straight
    if is_straight:
        return (4, straight_high)
    # Three of a kind
    if 3 in cnt.values():
        triple = next(r for r, c in cnt.items() if c == 3)
        kickers = sorted([r for r, c in cnt.items() if c == 1], reverse=True)
        return (3, triple) + tuple(kickers)
    # Two pair
    pairs = [r for r, c in cnt.items() if c == 2]
    if len(pairs) == 2:
        high_pair = max(pairs)
        low_pair = min(pairs)
        kicker = next(r for r, c in cnt.items() if c == 1)
        return (2, high_pair, low_pair, kicker)
    # One pair
    if len(pairs) == 1:
        pair = pairs[0]
        kickers = sorted([r for r, c in cnt.items() if c == 1], reverse=True)
        return (1, pair) + tuple(kickers)
    # High card
    return (0,) + tuple(sorted(ranks, reverse=True))


def best_hand(cards):
    """
    Given a list of cards (≥5) return the rank tuple of the strongest 5‑card hand.
    """
    best = None
    for combo in combinations(cards, 5):
        r = rank_hand(combo)
        if best is None or r > best:
            best = r
    return best

# ------------------------------------------------------------
# Equity calculations
# ------------------------------------------------------------
def compute_exact_equity(state):
    """
    Exact equity when the board already contains five community cards.
    Enumerate opponent private cards (max 51) and compare best hands.
    """
    private = state['private_cards']
    board = state['public_cards']
    # All cards that are already on the table / in our hand
    known = {card_to_tuple(c) for c in private + board}
    # Build full deck
    deck = [(r, s) for r in RANKS for s in SUITS]
    opponent_options = [c for c in deck if c not in known]
    total = len(opponent_options)
    wins = 0
    ties = 0
    for opp_card in opponent_options:
        opp_hand = [tuple_to_card(opp_card)] + board
        my_hand = private + board
        my_rank = best_hand(my_hand)
        opp_rank = best_hand(opp_hand)
        if my_rank > opp_rank:
            wins += 1
        elif my_rank == opp_rank:
            ties += 0.5
    return (wins + ties) / total


def compute_monte_carlo_equity(state, samples=300):
    """
    Approximate equity when fewer than five community cards are known.
    Sample opponent private card and the missing community cards uniformly
    from the remaining deck, then evaluate the best 5‑card hand for each.
    """
    private = state['private_cards']
    board_partial = state['public_cards']
    board_len = len(board_partial)

    # Cards already known (including ours)
    known = {card_to_tuple(c) for c in private + board_partial}
    deck = [(r, s) for r in RANKS for s in SUITS]
    remaining = [c for c in deck if c not in known]

    wins = 0
    ties = 0
    for _ in range(samples):
        opp_card = random.choice(remaining)
        # Remove opponent private from pool before sampling future board cards
        pool = [c for c in remaining if c != opp_card]
        board_needed = 5 - board_len
        future_board = random.sample(pool, board_needed)
        full_board = [tuple_to_card(c) for c in board_partial + future_board]

        my_hand = private + full_board
        opp_hand = [tuple_to_card(opp_card)] + full_board

        my_rank = best_hand(my_hand)
        opp_rank = best_hand(opp_hand)

        if my_rank > opp_rank:
            wins += 1
        elif my_rank == opp_rank:
            ties += 0.5
    return (wins + ties) / samples


def estimate_equity(state):
    """Pick the exact calculation when possible, otherwise Monte‑Carlo."""
    if len(state['public_cards']) == 5:
        return compute_exact_equity(state)
    else:
        return compute_monte_carlo_equity(state)

# ------------------------------------------------------------
# Decision making
# ------------------------------------------------------------
TOTAL_STACK = 100  # assumed initial stack size (can be tuned if needed)

def decide_action(state, equity):
    actions = set(state['allowed_actions'])
    pot = state['pot']
    to_call = state['to_call']
    my_spent = state['my_spent']
    remaining = TOTAL_STACK - my_spent

    # Pot‑odds for a call when there is a bet to face
    required_eq = to_call / (pot + to_call) if to_call > 0 else 0.5

    # Helper to see if equity comfortably exceeds the odds
    def strong_enough(margin=0.07):
        return equity > required_eq + margin

    # ----- Aggressive actions (raise / all‑in) -----
    if 'raise' in actions:
        if to_call == 0:
            # Free street: need a modest edge to bet
            if equity > 0.55:
                if 'all-in' in actions and (equity > 0.9 or remaining <= 10):
                    return 'all-in'
                return 'raise'
        else:
            if strong_enough():
                if 'all-in' in actions and (equity > 0.9 or remaining <= to_call + 10):
                    return 'all-in'
                return 'raise'

    # ----- Call / Check -----
    if 'call' in actions:
        if to_call > 0:
            if equity >= required_eq:
                return 'call'
        else:
            # To‑call == 0 → a check
            if equity >= 0.5:
                return 'call'
            # If equity is very low but folding is not allowed, we are forced to check
            if 'fold' not in actions:
                return 'call'

    # ----- Fold (if allowed) -----
    if 'fold' in actions:
        return 'fold'

    # ----- All‑in fallback (rare) -----
    if 'all-in' in actions:
        return 'all-in'

    # Final fallback (should never be reached because a legal action is guaranteed)
    return 'call'

# ------------------------------------------------------------
# Public policy API
# ------------------------------------------------------------
def policy(state: dict) -> str:
    """
    Return one of {'fold','call','raise','all-in'} according to the
    heuristic described above.
    """
    equity = estimate_equity(state)
    return decide_action(state, equity)
