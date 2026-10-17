
from functools import lru_cache
import time

SIZE = 4

# All 4-in-a-row winning lines on a 4x4 board.
LINES = (
    (0, 1, 2, 3),
    (4, 5, 6, 7),
    (8, 9, 10, 11),
    (12, 13, 14, 15),
    (0, 4, 8, 12),
    (1, 5, 9, 13),
    (2, 6, 10, 14),
    (3, 7, 11, 15),
    (0, 5, 10, 15),
    (3, 6, 9, 12),
)

# Prefer cells that participate in more strong lines.
CELL_WEIGHTS = (
    4, 2, 2, 4,
    2, 5, 5, 2,
    2, 5, 5, 2,
    4, 2, 2, 4,
)

# Good opening preference order.
OPENING_ORDER = (
    5, 6, 9, 10,   # inner 2x2
    0, 3, 12, 15,  # corners
    1, 2, 4, 7, 8, 11, 13, 14
)

# Value of unblocked lines containing k marks from one side.
LINE_WEIGHTS = (0, 3, 20, 120, 0)

WIN_SCORE = 1_000_000
INF = 10_000_000

EXACT = 0
LOWER = 1
UPPER = 2


def _play(state, idx, player):
    return state[:idx] + (player,) + state[idx + 1:]


def _idx_to_rc(idx):
    return (idx // 4, idx % 4)


@lru_cache(maxsize=100000)
def _winner(state):
    for a, b, c, d in LINES:
        s = state[a] + state[b] + state[c] + state[d]
        if s == 4:
            return 1
        if s == -4:
            return -1
    return 0


@lru_cache(maxsize=200000)
def _winning_moves(state, player):
    """Return sorted tuple of empty cells where `player` wins immediately."""
    target = 3 * player
    out = set()

    for a, b, c, d in LINES:
        s = state[a] + state[b] + state[c] + state[d]
        if s != target:
            continue

        zero = -1
        if state[a] == 0:
            zero = a
        elif state[b] == 0:
            zero = b
        elif state[c] == 0:
            zero = c
        elif state[d] == 0:
            zero = d

        if zero != -1:
            out.add(zero)

    return tuple(sorted(out))


@lru_cache(maxsize=100000)
def _heuristic_abs(state):
    """Heuristic from player-1's perspective."""
    w = _winner(state)
    if w != 0:
        return w * (WIN_SCORE + state.count(0))

    score = 0

    # Cell preference
    for i, v in enumerate(state):
        score += v * CELL_WEIGHTS[i]

    # Open-line value
    for a, b, c, d in LINES:
        v0, v1, v2, v3 = state[a], state[b], state[c], state[d]
        c1 = (v0 == 1) + (v1 == 1) + (v2 == 1) + (v3 == 1)
        c2 = (v0 == -1) + (v1 == -1) + (v2 == -1) + (v3 == -1)

        if c1 and c2:
            continue
        if c1:
            score += LINE_WEIGHTS[c1]
        elif c2:
            score -= LINE_WEIGHTS[c2]

    # Immediate threat count matters a lot.
    score += 70 * (len(_winning_moves(state, 1)) - len(_winning_moves(state, -1)))

    return int(score)


def _move_order_score(state, player, idx, tt_move=None):
    score = 0

    if tt_move is not None and idx == tt_move:
        score += 1_000_000_000

    score += CELL_WEIGHTS[idx] * 10

    child = _play(state, idx, player)

    if _winner(child) == player:
        return score + 100_000_000

    opp_wins = _winning_moves(child, -player)
    if opp_wins:
        score -= 200_000 + 5_000 * len(opp_wins)

    my_wins = _winning_moves(child, player)
    if not opp_wins and len(my_wins) >= 2:
        score += 150_000 + 1_000 * len(my_wins)

    score += player * _heuristic_abs(child)
    return score


def _ordered_moves(state, player, tt_move=None):
    moves = [i for i, v in enumerate(state) if v == 0]
    moves.sort(key=lambda m: _move_order_score(state, player, m, tt_move), reverse=True)
    return moves


def policy(board: list[list[int]]) -> tuple[int, int]:
    state = tuple(board[r][c] for r in range(4) for c in range(4))
    empties = [i for i, v in enumerate(state) if v == 0]

    # No legal move exists only on a full board; this should not happen in normal play.
    if not empties:
        return (0, 0)

    # If somehow called on an already terminal board, still return a legal move.
    if _winner(state) != 0:
        return _idx_to_rc(empties[0])

    num_us = state.count(1)
    num_them = state.count(-1)

    # Opening book
    if len(empties) == 16:
        return (1, 1)
    if num_us == 0 and num_them == 1:
        for idx in OPENING_ORDER:
            if state[idx] == 0:
                return _idx_to_rc(idx)

    # Tactical layer: win now if possible.
    my_wins = _winning_moves(state, 1)
    if my_wins:
        best = max(my_wins, key=lambda m: CELL_WEIGHTS[m])
        return _idx_to_rc(best)

    # Tactical layer: forced blocks.
    opp_wins = _winning_moves(state, -1)
    if len(opp_wins) == 1:
        return _idx_to_rc(opp_wins[0])

    # If opponent has multiple immediate wins, this is usually lost.
    # Still return a legal blocking move.
    if len(opp_wins) >= 2:
        best = max(opp_wins, key=lambda m: CELL_WEIGHTS[m])
        return _idx_to_rc(best)

    # Root move filtering: avoid moves that lose immediately if possible.
    ordered = _ordered_moves(state, 1)
    safe_moves = []
    for m in ordered:
        child = _play(state, m, 1)
        opp_after = _winning_moves(child, -1)
        if not opp_after:
            safe_moves.append(m)
            # Immediate fork / double-threat win.
            if len(_winning_moves(child, 1)) >= 2:
                return _idx_to_rc(m)

    root_moves = safe_moves if safe_moves else ordered
    if not root_moves:
        return _idx_to_rc(empties[0])
    if len(root_moves) == 1:
        return _idx_to_rc(root_moves[0])

    # Search depth schedule
    n = len(empties)
    if n <= 8:
        max_depth = n
    elif n <= 10:
        max_depth = 10
    elif n <= 12:
        max_depth = 8
    else:
        max_depth = 6

    start = time.perf_counter()
    TIME_LIMIT = 0.88
    tt = {}
    nodes = 0

    def negamax(pos, player, depth, alpha, beta):
        nonlocal nodes
        nodes += 1
        if (nodes & 255) == 0 and time.perf_counter() - start > TIME_LIMIT:
            raise TimeoutError

        empties_left = pos.count(0)
        w = _winner(pos)
        if w != 0:
            return w * player * (WIN_SCORE + empties_left)
        if empties_left == 0:
            return 0

        # Exact tactical pruning
        my_now = _winning_moves(pos, player)
        if my_now:
            return WIN_SCORE + empties_left

        opp_now = _winning_moves(pos, -player)
        if len(opp_now) >= 2:
            return -(WIN_SCORE + empties_left)

        if depth == 0:
            return player * _heuristic_abs(pos)

        key = (pos, player)
        orig_alpha = alpha
        orig_beta = beta
        tt_move = None

        entry = tt.get(key)
        if entry is not None:
            entry_depth, entry_score, entry_flag, entry_move = entry
            tt_move = entry_move
            if entry_depth >= depth:
                if entry_flag == EXACT:
                    return entry_score
                elif entry_flag == LOWER:
                    alpha = max(alpha, entry_score)
                else:
                    beta = min(beta, entry_score)
                if alpha >= beta:
                    return entry_score

        # If opponent has exactly one immediate win next turn, we must block it.
        if len(opp_now) == 1:
            moves = list(opp_now)
        else:
            moves = _ordered_moves(pos, player, tt_move)

        best_score = -INF
        best_move_local = moves[0] if moves else None

        for m in moves:
            child = _play(pos, m, player)
            score = -negamax(child, -player, depth - 1, -beta, -alpha)

            if score > best_score:
                best_score = score
                best_move_local = m

            if score > alpha:
                alpha = score
            if alpha >= beta:
                break

        flag = EXACT
        if best_score <= orig_alpha:
            flag = UPPER
        elif best_score >= orig_beta:
            flag = LOWER

        tt[key] = (depth, best_score, flag, best_move_local)
        return best_score

    best_move = root_moves[0]

    try:
        for depth in range(1, max_depth + 1):
            if time.perf_counter() - start > TIME_LIMIT:
                break

            root_entry = tt.get((state, 1))
            tt_move = root_entry[3] if root_entry is not None else None

            moves = sorted(
                root_moves,
                key=lambda m: _move_order_score(state, 1, m, tt_move),
                reverse=True,
            )

            current_best_move = best_move
            current_best_score = -INF
            alpha = -INF
            beta = INF

            for m in moves:
                child = _play(state, m, 1)
                score = -negamax(child, -1, depth - 1, -beta, -alpha)

                if score > current_best_score:
                    current_best_score = score
                    current_best_move = m

                if score > alpha:
                    alpha = score

            best_move = current_best_move
            tt[(state, 1)] = (depth, current_best_score, EXACT, best_move)

            if abs(current_best_score) >= WIN_SCORE:
                break

    except TimeoutError:
        pass

    # Final legality fallback
    if state[best_move] != 0:
        best_move = empties[0]

    return _idx_to_rc(best_move)
