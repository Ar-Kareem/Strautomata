
from functools import lru_cache

N = 4

# All winning lines on a 4x4 board: 4 rows, 4 columns, 2 diagonals.
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

# Move ordering: central cells first, then corners, then edges.
ORDER = (5, 6, 9, 10, 0, 3, 12, 15, 1, 2, 4, 7, 8, 11, 13, 14)


def _winner(flat):
    """Return 1 if player 1 has won, -1 if player -1 has won, else 0."""
    for line in LINES:
        s = flat[line[0]] + flat[line[1]] + flat[line[2]] + flat[line[3]]
        if s == 4:
            return 1
        if s == -4:
            return -1
    return 0


def _legal_moves(flat):
    return [i for i in ORDER if flat[i] == 0]


def _move_score_heuristic(flat, idx, player):
    """
    Lightweight ordering heuristic:
    prefer moves that create/extend unblocked lines and interfere with opponent lines.
    """
    score = 0
    for line in LINES:
        if idx in line:
            vals = [flat[j] for j in line]
            own = vals.count(player)
            opp = vals.count(-player)
            if opp == 0:
                score += 10 ** own
            if own == 0:
                score += 8 ** opp
    return score


@lru_cache(maxsize=None)
def _negamax(state, player, alpha, beta):
    """
    Return score from current player's perspective.
    Scores prefer quicker wins and slower losses.
    """
    flat = state
    w = _winner(flat)
    if w == player:
        return 1000 + flat.count(0)
    if w == -player:
        return -1000 - flat.count(0)

    moves = _legal_moves(flat)
    if not moves:
        return 0

    # Tactical move ordering improves alpha-beta pruning.
    moves.sort(key=lambda m: _move_score_heuristic(flat, m, player), reverse=True)

    best = -100000
    for m in moves:
        nxt = list(flat)
        nxt[m] = player
        val = -_negamax(tuple(nxt), -player, -beta, -alpha)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best


def _immediate_move(flat, player):
    """Return a winning move for player if available, else None."""
    for m in _legal_moves(flat):
        nxt = list(flat)
        nxt[m] = player
        if _winner(nxt) == player:
            return m
    return None


def _fallback_move(flat):
    """Always return some legal move, preferring strong board positions."""
    for m in ORDER:
        if flat[m] == 0:
            return divmod(m, 4)
    return (0, 0)  # Should never occur for valid non-full boards.


def policy(board: list[list[int]]) -> tuple[int, int]:
    try:
        flat = tuple(board[r][c] for r in range(4) for c in range(4))

        # If the board is invalid/full for any reason, still attempt a legal-ish fallback.
        if not any(v == 0 for v in flat):
            return (0, 0)

        # 1. Win immediately if possible.
        win = _immediate_move(flat, 1)
        if win is not None:
            return divmod(win, 4)

        # 2. Block opponent's immediate win.
        block = _immediate_move(flat, -1)
        if block is not None:
            return divmod(block, 4)

        # 3. Exact minimax/negamax search.
        best_move = None
        best_val = -100000
        alpha = -100000
        beta = 100000

        moves = _legal_moves(flat)
        moves.sort(key=lambda m: _move_score_heuristic(flat, m, 1), reverse=True)

        for m in moves:
            nxt = list(flat)
            nxt[m] = 1
            val = -_negamax(tuple(nxt), -1, -beta, -alpha)
            if val > best_val:
                best_val = val
                best_move = m
            if val > alpha:
                alpha = val

        if best_move is not None and flat[best_move] == 0:
            return divmod(best_move, 4)

        return _fallback_move(flat)

    except Exception:
        # Absolute safety: never fail to return a legal empty cell if the board is usable.
        try:
            flat = [board[r][c] for r in range(4) for c in range(4)]
            return _fallback_move(flat)
        except Exception:
            return (0, 0)
