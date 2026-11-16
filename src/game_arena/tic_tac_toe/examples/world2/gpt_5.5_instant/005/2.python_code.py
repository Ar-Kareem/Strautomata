
from functools import lru_cache

N = 4
WIN_LINES = []

# rows and columns
for i in range(N):
    WIN_LINES.append(tuple((i, j) for j in range(N)))
    WIN_LINES.append(tuple((j, i) for j in range(N)))

# diagonals
WIN_LINES.append(tuple((i, i) for i in range(N)))
WIN_LINES.append(tuple((i, N - 1 - i) for i in range(N)))

# Move ordering: central squares first, then corners/edges
MOVE_ORDER = [
    (1, 1), (1, 2), (2, 1), (2, 2),
    (0, 0), (0, 3), (3, 0), (3, 3),
    (0, 1), (0, 2), (1, 0), (1, 3),
    (2, 0), (2, 3), (3, 1), (3, 2),
]

POS_WEIGHT = [
    [3, 4, 4, 3],
    [4, 6, 6, 4],
    [4, 6, 6, 4],
    [3, 4, 4, 3],
]


def _flatten(board):
    return tuple(board[r][c] for r in range(N) for c in range(N))


def _winner(state):
    for line in WIN_LINES:
        s = 0
        for r, c in line:
            s += state[r * N + c]
        if s == N:
            return 1
        if s == -N:
            return -1
    return 0


def _legal_moves(state):
    return [m for m in MOVE_ORDER if state[m[0] * N + m[1]] == 0]


def _make_move(state, move, player):
    idx = move[0] * N + move[1]
    lst = list(state)
    lst[idx] = player
    return tuple(lst)


def _static_eval(state):
    w = _winner(state)
    if w == 1:
        return 1000000
    if w == -1:
        return -1000000

    score = 0

    # Positional score
    for r in range(N):
        for c in range(N):
            v = state[r * N + c]
            if v:
                score += v * POS_WEIGHT[r][c]

    # Line/threat score
    my_threes = 0
    opp_threes = 0
    my_twos = 0
    opp_twos = 0

    for line in WIN_LINES:
        vals = [state[r * N + c] for r, c in line]
        mine = vals.count(1)
        opp = vals.count(-1)
        empty = vals.count(0)

        if opp == 0:
            if mine == 3 and empty == 1:
                score += 600
                my_threes += 1
            elif mine == 2 and empty == 2:
                score += 80
                my_twos += 1
            elif mine == 1 and empty == 3:
                score += 8
        if mine == 0:
            if opp == 3 and empty == 1:
                score -= 700
                opp_threes += 1
            elif opp == 2 and empty == 2:
                score -= 90
                opp_twos += 1
            elif opp == 1 and empty == 3:
                score -= 9

    # Fork pressure
    if my_threes >= 2:
        score += 2500
    if opp_threes >= 2:
        score -= 3000
    if my_twos >= 2:
        score += 120
    if opp_twos >= 2:
        score -= 140

    return score


def _immediate_winning_move(state, player):
    for move in _legal_moves(state):
        if _winner(_make_move(state, move, player)) == player:
            return move
    return None


@lru_cache(maxsize=None)
def _minimax(state, player, alpha, beta):
    w = _winner(state)
    if w == 1:
        return 1000000 + sum(1 for x in state if x == 0)
    if w == -1:
        return -1000000 - sum(1 for x in state if x == 0)

    moves = _legal_moves(state)
    if not moves:
        return 0

    empties = len(moves)

    # Full search is feasible for much of 4x4; use static cutoff early.
    # Immediate tactical positions are still accurately handled.
    if empties > 10:
        return _static_eval(state)

    if player == 1:
        best = -10**9
        for move in moves:
            ns = _make_move(state, move, 1)
            val = _minimax(ns, -1, alpha, beta)
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        return best
    else:
        best = 10**9
        for move in moves:
            ns = _make_move(state, move, -1)
            val = _minimax(ns, 1, alpha, beta)
            if val < best:
                best = val
            if best < beta:
                beta = best
            if alpha >= beta:
                break
        return best


def policy(board: list[list[int]]) -> tuple[int, int]:
    try:
        state = _flatten(board)
        legal = _legal_moves(state)

        # Absolute safety fallback
        if not legal:
            return (0, 0)

        # Win immediately if possible.
        move = _immediate_winning_move(state, 1)
        if move is not None:
            return move

        # Block opponent's immediate win.
        move = _immediate_winning_move(state, -1)
        if move is not None:
            return move

        # Prefer opening central control.
        if len(legal) >= 15:
            for m in [(1, 1), (1, 2), (2, 1), (2, 2)]:
                if state[m[0] * N + m[1]] == 0:
                    return m

        best_move = legal[0]
        best_val = -10**9
        alpha = -10**9
        beta = 10**9

        for move in legal:
            ns = _make_move(state, move, 1)

            # If this move allows an immediate opponent win, penalize unless unavoidable.
            opp_win = _immediate_winning_move(ns, -1)
            if opp_win is not None:
                val = -900000
            else:
                val = _minimax(ns, -1, alpha, beta)

            # Small tie-breaker using position weights.
            val += POS_WEIGHT[move[0]][move[1]]

            if val > best_val:
                best_val = val
                best_move = move

            if val > alpha:
                alpha = val

        # Final legality check.
        r, c = best_move
        if 0 <= r < N and 0 <= c < N and board[r][c] == 0:
            return (r, c)

        for r in range(N):
            for c in range(N):
                if board[r][c] == 0:
                    return (r, c)

        return (0, 0)
    except Exception:
        # Never fail to return a legal move if any exists.
        for r in range(4):
            for c in range(4):
                try:
                    if board[r][c] == 0:
                        return (r, c)
                except Exception:
                    pass
        return (0, 0)
