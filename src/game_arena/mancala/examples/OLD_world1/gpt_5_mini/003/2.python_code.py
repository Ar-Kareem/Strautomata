
# Kalah move-selection policy
# Always returns a legal house index 0..5 with you[i] > 0

from typing import List, Tuple
import math
from functools import lru_cache

# Maximum search depth (plies). Reasonable tradeoff for 1s limit.
MAX_DEPTH = 7

def apply_move(side: List[int], opp: List[int], i: int) -> Tuple[List[int], List[int], bool, bool]:
    """
    Apply a move taken from house i of 'side' (0..5).
    Returns (new_side, new_opp, extra_turn, game_over).
    side and opp are lists length 7: houses 0..5 and store at 6.
    """
    # Build positional board: indices 0..5 side houses, 6 side store,
    # 7..12 opp houses (0..5), 13 opp store.
    pos = [0] * 14
    for k in range(6):
        pos[k] = side[k]
    pos[6] = side[6]
    for k in range(6):
        pos[7 + k] = opp[k]
    pos[13] = opp[6]

    s = i
    seeds = pos[s]
    pos[s] = 0
    j = s
    # sow seeds, skipping index 13 (opponent store)
    while seeds > 0:
        j = (j + 1) % 14
        if j == 13:
            # skip opponent store
            continue
        pos[j] += 1
        seeds -= 1

    extra_turn = (j == 6)

    # Capture: if last seed landed in side house 0..5, and it was empty before the drop (i.e., now equal 1),
    # and opposite house has seeds, capture both into side store (6).
    if 0 <= j <= 5:
        opp_index = 12 - j  # mapping: 0<->12, 1<->11, ..., 5<->7
        if pos[j] == 1 and pos[opp_index] > 0:
            captured = pos[j] + pos[opp_index]
            pos[6] += captured
            pos[j] = 0
            pos[opp_index] = 0

    # Check end game: one side houses empty
    sum_side_houses = sum(pos[0:6])
    sum_opp_houses = sum(pos[7:13])
    game_over = False
    if sum_side_houses == 0 or sum_opp_houses == 0:
        game_over = True
        # collect remaining seeds into respective stores
        if sum_side_houses == 0:
            # move opp houses to opp store (13)
            rem = sum_opp_houses
            pos[13] += rem
            for k in range(7, 13):
                pos[k] = 0
        else:
            # move side houses to side store (6)
            rem = sum_side_houses
            pos[6] += rem
            for k in range(0, 6):
                pos[k] = 0

    # Convert back to side and opp lists
    new_side = [pos[k] for k in range(6)] + [pos[6]]
    new_opp = [pos[7 + k] for k in range(6)] + [pos[13]]
    return new_side, new_opp, extra_turn, game_over

def evaluate(you: Tuple[int, ...], opp: Tuple[int, ...]) -> float:
    """
    Heuristic evaluation from the perspective of 'you' (maximizer).
    Primary factor: store difference. Secondary: seeds on side.
    """
    store_diff = you[6] - opp[6]
    house_diff = sum(you[0:6]) - sum(opp[0:6])
    # Weight stores heavily; houses less so. Extra small tie-breaker for more moves.
    return float(store_diff) + 0.12 * float(house_diff)

def legal_moves(state_side: List[int]) -> List[int]:
    """Return indices 0..5 of non-empty houses."""
    return [i for i in range(6) if state_side[i] > 0]

# Transposition cache: map (you_tuple, opp_tuple, depth, maximizing) -> value
# Use LRU cache via a helper wrapper for minimax recursion
def policy(you: List[int], opponent: List[int]) -> int:
    """
    Select a legal house index 0..5 to move from.
    """

    you_t = tuple(you)
    opp_t = tuple(opponent)

    @lru_cache(maxsize=200000)
    def minimax(you_state: Tuple[int, ...], opp_state: Tuple[int, ...], depth: int, alpha: float, beta: float, maximizing: bool) -> float:
        """
        Minimax with alpha-beta pruning.
        you_state and opp_state are tuples length 7; they represent the board
        from the viewpoint where 'you_state' is the maximizer's side and 'opp_state' the opponent's.
        maximizing=True when it's maximizer's turn (we), False when it's opponent's turn.
        """
        # Terminal or depth limit
        # Quick terminal detection: if either side houses empty, move remaining to stores and evaluate
        if depth == 0:
            return evaluate(you_state, opp_state)

        # If game over in current state
        if sum(you_state[0:6]) == 0 or sum(opp_state[0:6]) == 0:
            # finalize
            you_end = list(you_state)
            opp_end = list(opp_state)
            if sum(you_end[0:6]) == 0:
                # opponent collects
                rem = sum(opp_end[0:6])
                opp_end[6] += rem
                for k in range(6):
                    opp_end[k] = 0
            else:
                rem = sum(you_end[0:6])
                you_end[6] += rem
                for k in range(6):
                    you_end[k] = 0
            return evaluate(tuple(you_end), tuple(opp_end))

        if maximizing:
            best = -math.inf
            moves = [i for i in range(6) if you_state[i] > 0]
            if not moves:
                # No legal moves — shouldn't occur per problem, but handle
                return evaluate(you_state, opp_state)
            # Move ordering: try moves that immediately give extra turn or capture first
            scored_moves = []
            for m in moves:
                ns, no, extra, game_over = apply_move(list(you_state), list(opp_state), m)
                score_quick = (ns[6] - no[6]) + 0.1 * (sum(ns[0:6]) - sum(no[0:6]))
                if extra:
                    score_quick += 0.5
                scored_moves.append(( -score_quick, m))  # negative because we'll sort ascending
            scored_moves.sort()
            ordered_moves = [m for (_, m) in scored_moves]

            for m in ordered_moves:
                ns, no, extra, game_over = apply_move(list(you_state), list(opp_state), m)
                ns_t = tuple(ns)
                no_t = tuple(no)
                if game_over:
                    val = evaluate(ns_t, no_t)
                else:
                    if extra:
                        val = minimax(ns_t, no_t, depth - 1, alpha, beta, True)
                    else:
                        # opponent moves next: swap roles
                        val = minimax(no_t, ns_t, depth - 1, alpha, beta, False)
                if val > best:
                    best = val
                if best > alpha:
                    alpha = best
                if beta <= alpha:
                    break  # beta cut-off
            return best
        else:
            # minimizing (opponent to move)
            worst = math.inf
            moves = [i for i in range(6) if opp_state[i] > 0]
            if not moves:
                return evaluate(you_state, opp_state)
            # Order opponent moves similarly (opponent prefers high immediate value for them)
            scored_moves = []
            for m in moves:
                ns, no, extra, game_over = apply_move(list(opp_state), list(you_state), m)
                # ns is opponent side after move, no is our side after move (note mapping)
                # Quick heuristic from opponent's perspective:
                score_quick = (ns[6] - no[6]) + 0.1 * (sum(ns[0:6]) - sum(no[0:6]))
                if extra:
                    score_quick += 0.5
                scored_moves.append((score_quick, m))
            # opponent will try to maximize their score -> from our minimax perspective we order by descending
            scored_moves.sort(reverse=True)
            ordered_moves = [m for (_, m) in scored_moves]

            for m in ordered_moves:
                ns, no, extra, game_over = apply_move(list(opp_state), list(you_state), m)
                # map back: after calling with side=opp_state, ns is new opp, no is new you
                new_you_t = tuple(no)
                new_opp_t = tuple(ns)
                if game_over:
                    val = evaluate(new_you_t, new_opp_t)
                else:
                    if extra:
                        # opponent moves again (still minimizing)
                        val = minimax(new_you_t, new_opp_t, depth - 1, alpha, beta, False)
                    else:
                        # our turn next (maximizer)
                        val = minimax(new_you_t, new_opp_t, depth - 1, alpha, beta, True)
                if val < worst:
                    worst = val
                if worst < beta:
                    beta = worst
                if beta <= alpha:
                    break  # alpha cut-off
            return worst

    # Top-level decision: evaluate each legal move using minimax and choose best
    moves = legal_moves(you)
    if not moves:
        # Should not happen by problem statement, but pick 0 defensively
        return 0

    best_move = moves[0]
    best_val = -math.inf
    # Quick ordering: evaluate immediate benefit
    scored = []
    for m in moves:
        ns, no, extra, game_over = apply_move(list(you), list(opponent), m)
        quick = (ns[6] - no[6]) + 0.1 * (sum(ns[0:6]) - sum(no[0:6]))
        if extra:
            quick += 0.5
        scored.append((-quick, m))
    scored.sort()
    ordered_moves = [m for (_, m) in scored]

    # Search each move with minimax
    for m in ordered_moves:
        ns, no, extra, game_over = apply_move(list(you), list(opponent), m)
        ns_t = tuple(ns)
        no_t = tuple(no)
        if game_over:
            val = evaluate(ns_t, no_t)
        else:
            if extra:
                val = minimax(ns_t, no_t, MAX_DEPTH - 1, -math.inf, math.inf, True)
            else:
                val = minimax(no_t, ns_t, MAX_DEPTH - 1, -math.inf, math.inf, False)
        # prefer higher value; tie-breaker prefer extra move and lower house index
        if val > best_val + 1e-9:
            best_val = val
            best_move = m
        elif abs(val - best_val) <= 1e-9:
            # tie-breaker: prefer move that gives extra move
            _, _, extra_curr, _ = apply_move(list(you), list(opponent), best_move)
            if extra and not extra_curr:
                best_move = m
            elif extra == extra_curr:
                if m < best_move:
                    best_move = m

    return int(best_move)
