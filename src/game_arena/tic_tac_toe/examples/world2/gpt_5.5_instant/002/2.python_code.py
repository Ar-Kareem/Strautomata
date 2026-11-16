
from functools import lru_cache

N = 4

# All winning lines: 4 rows, 4 cols, 2 diagonals
LINES = (
    ((0, 0), (0, 1), (0, 2), (0, 3)),
    ((1, 0), (1, 1), (1, 2), (1, 3)),
    ((2, 0), (2, 1), (2, 2), (2, 3)),
    ((3, 0), (3, 1), (3, 2), (3, 3)),
    ((0, 0), (1, 0), (2, 0), (3, 0)),
    ((0, 1), (1, 1), (2, 1), (3, 1)),
    ((0, 2), (1, 2), (2, 2), (3, 2)),
    ((0, 3), (1, 3), (2, 3), (3, 3)),
    ((0, 0), (1, 1), (2, 2), (3, 3)),
    ((0, 3), (1, 2), (2, 1), (3, 0)),
)

# Good static ordering for alpha-beta and for fallback play.
ORDER = (
    (1, 1), (1, 2), (2, 1), (2, 2),
    (0, 0), (0, 3), (3, 0), (3, 3),
    (0, 1), (0, 2), (1, 0), (1, 3),
    (2, 0), (2, 3), (3, 1), (3, 2),
)


def _flat(board):
    return tuple(board[r][c] for r in range(4) for c in range(4))


def _winner(state):
    for line in LINES:
        s = 0
        for r, c in line:
            s += state[r * 4 + c]
        if s == 4:
            return 1
        if s == -4:
            return -1
    return 0


def _legal_moves(state):
    return [(r, c) for r, c in ORDER if state[r * 4 + c] == 0]


def _would_win(state, move, player):
    idx = move[0] * 4 + move[1]
    if state[idx] != 0:
        return False
    lst = list(state)
    lst[idx] = player
    return _winner(tuple(lst)) == player


def _heuristic(state):
    """
    Static evaluation from player 1's perspective.
    Used only as a safety fallback in unlikely timeout/deep situations.
    """
    score = 0
    weights = {0: 0, 1: 1, 2: 8, 3: 80, 4: 10000}
    for line in LINES:
        vals = [state[r * 4 + c] for r, c in line]
        a = vals.count(1)
        b = vals.count(-1)
        if a and b:
            continue
        if a:
            score += weights[a]
        elif b:
            score -= weights[b]
    # small positional bonus
    for r, c in ((1, 1), (1, 2), (2, 1), (2, 2)):
        score += 2 * state[r * 4 + c]
    for r, c in ((0, 0), (0, 3), (3, 0), (3, 3)):
        score += state[r * 4 + c]
    return score


@lru_cache(maxsize=None)
def _negamax(state, player, alpha, beta):
    """
    Returns score from side-to-move's perspective.
    Positive means current player can force a favorable result.
    Scores include depth preference: faster wins and slower losses.
    """
    w = _winner(state)
    if w != 0:
        # Previous player just won, so side to move has lost.
        empties = state.count(0)
        return -1000 - empties

    moves = _legal_moves(state)
    if not moves:
        return 0

    best = -10**9

    # Tactical ordering: winning moves first, then blocking moves, then positional order.
    winning = []
    blocking = []
    others = []
    opp = -player
    for mv in moves:
        if _would_win(state, mv, player):
            winning.append(mv)
        elif _would_win(state, mv, opp):
            blocking.append(mv)
        else:
            others.append(mv)
    ordered = winning + blocking + others

    for r, c in ordered:
        idx = r * 4 + c
        lst = list(state)
        lst[idx] = player
        child = tuple(lst)
        val = -_negamax(child, -player, -beta, -alpha)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best


def _best_by_heuristic(state):
    best_move = None
    best_score = -10**18
    for r, c in _legal_moves(state):
        idx = r * 4 + c
        lst = list(state)
        lst[idx] = 1
        child = tuple(lst)
        w = _winner(child)
        if w == 1:
            score = 10**9
        else:
            # Assume opponent replies; simple minimax-ish one-ply safety.
            opp_moves = _legal_moves(child)
            if not opp_moves:
                score = _heuristic(child)
            else:
                worst = 10**18
                for rr, cc in opp_moves:
                    j = rr * 4 + cc
                    lst2 = list(child)
                    lst2[j] = -1
                    child2 = tuple(lst2)
                    if _winner(child2) == -1:
                        val = -10**9
                    else:
                        val = _heuristic(child2)
                    if val < worst:
                        worst = val
                score = worst
        if score > best_score:
            best_score = score
            best_move = (r, c)
    return best_move


def policy(board: list[list[int]]) -> tuple[int, int]:
    try:
        state = _flat(board)
        legal = _legal_moves(state)
        if not legal:
            # No legal move exists, but return a valid-shaped tuple.
            return (0, 0)

        # Immediate win.
        for mv in legal:
            if _would_win(state, mv, 1):
                return mv

        # Immediate block.
        for mv in legal:
            if _would_win(state, mv, -1):
                return mv

        best_move = legal[0]
        best_score = -10**9

        # Full cached alpha-beta solver.
        for r, c in legal:
            idx = r * 4 + c
            lst = list(state)
            lst[idx] = 1
            child = tuple(lst)

            if _winner(child) == 1:
                score = 10**9
            else:
                score = -_negamax(child, -1, -10**9, 10**9)

            # Tie-break by ORDER because legal is already ordered.
            if score > best_score:
                best_score = score
                best_move = (r, c)

        return best_move

    except Exception:
        # Absolute safety: always return an empty square if one exists.
        try:
            for r in range(4):
                for c in range(4):
                    if board[r][c] == 0:
                        return (r, c)
        except Exception:
            pass
        return (0, 0)
