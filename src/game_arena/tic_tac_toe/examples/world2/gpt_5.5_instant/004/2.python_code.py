
from functools import lru_cache
import time

N = 4
WIN_LINES = []

# Rows
for r in range(N):
    WIN_LINES.append(tuple((r, c) for c in range(N)))
# Columns
for c in range(N):
    WIN_LINES.append(tuple((r, c) for r in range(N)))
# Diagonals
WIN_LINES.append(tuple((i, i) for i in range(N)))
WIN_LINES.append(tuple((i, N - 1 - i) for i in range(N)))

# Good move ordering for 4x4: near-centers first, then corners/edges
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


def _winner_tuple(state):
    """Return 1 if we have won, -1 if opponent has won, else 0."""
    for line in WIN_LINES:
        s = 0
        for r, c in line:
            s += state[r * N + c]
        if s == N:
            return 1
        if s == -N:
            return -1
    return 0


def _legal_moves_tuple(state):
    return [mv for mv in MOVE_ORDER if state[mv[0] * N + mv[1]] == 0]


def _heuristic(state):
    """Static evaluation from our perspective."""
    w = _winner_tuple(state)
    if w == 1:
        return 100000
    if w == -1:
        return -100000

    score = 0

    # Positional value
    for r in range(N):
        for c in range(N):
            v = state[r * N + c]
            if v == 1:
                score += POS_WEIGHT[r][c]
            elif v == -1:
                score -= POS_WEIGHT[r][c]

    # Line potential. Unblocked lines are valuable; near-complete lines are urgent.
    for line in WIN_LINES:
        ours = 0
        theirs = 0
        for r, c in line:
            v = state[r * N + c]
            if v == 1:
                ours += 1
            elif v == -1:
                theirs += 1

        if ours and theirs:
            continue
        if ours:
            if ours == 3:
                score += 900
            elif ours == 2:
                score += 80
            elif ours == 1:
                score += 8
        elif theirs:
            if theirs == 3:
                score -= 1000
            elif theirs == 2:
                score -= 90
            elif theirs == 1:
                score -= 9

    return score


def _terminal_or_full(state):
    return _winner_tuple(state) != 0 or all(x != 0 for x in state)


@lru_cache(maxsize=None)
def _minimax(state, turn, alpha, beta):
    """
    Alpha-beta minimax.
    turn: 1 for our move/max, -1 for opponent/min.
    alpha/beta are passed as small ints; cached states include them, which is okay for 4x4.
    """
    w = _winner_tuple(state)
    empty_count = state.count(0)

    if w == 1:
        return 1000000 + empty_count
    if w == -1:
        return -1000000 - empty_count
    if empty_count == 0:
        return 0

    # Full search is feasible most of the time, but use depth limiting early to stay safe.
    # Depth increases as the board fills.
    if empty_count >= 12:
        depth_limit = 5
    elif empty_count >= 9:
        depth_limit = 7
    else:
        depth_limit = empty_count

    return _search_depth(state, turn, depth_limit, alpha, beta)


def _search_depth(state, turn, depth, alpha, beta):
    w = _winner_tuple(state)
    empty_count = state.count(0)

    if w == 1:
        return 1000000 + empty_count
    if w == -1:
        return -1000000 - empty_count
    if empty_count == 0:
        return 0
    if depth <= 0:
        return _heuristic(state)

    moves = _legal_moves_tuple(state)

    # Tactical ordering: immediate winning/blocking moves first through heuristic child sorting.
    scored_moves = []
    for r, c in moves:
        idx = r * N + c
        lst = list(state)
        lst[idx] = turn
        child = tuple(lst)
        scored_moves.append((_heuristic(child), r, c, child))

    if turn == 1:
        scored_moves.sort(reverse=True, key=lambda x: x[0])
        best = -10**9
        for _, r, c, child in scored_moves:
            val = _search_depth(child, -1, depth - 1, alpha, beta)
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if beta <= alpha:
                break
        return best
    else:
        scored_moves.sort(key=lambda x: x[0])
        best = 10**9
        for _, r, c, child in scored_moves:
            val = _search_depth(child, 1, depth - 1, alpha, beta)
            if val < best:
                best = val
            if best < beta:
                beta = best
            if beta <= alpha:
                break
        return best


def _immediate_move(state, player):
    """Return a winning move for player if one exists."""
    for r, c in _legal_moves_tuple(state):
        idx = r * N + c
        lst = list(state)
        lst[idx] = player
        if _winner_tuple(tuple(lst)) == player:
            return (r, c)
    return None


def _creates_fork_score(state, move, player):
    """Count number of 3-in-a-row open threats after playing move."""
    r, c = move
    idx = r * N + c
    if state[idx] != 0:
        return -1
    lst = list(state)
    lst[idx] = player
    new_state = tuple(lst)

    threats = 0
    for line in WIN_LINES:
        vals = [new_state[rr * N + cc] for rr, cc in line]
        if vals.count(player) == 3 and vals.count(0) == 1:
            threats += 1
    return threats


def policy(board):
    """
    Return a legal move (row, col) for a 4x4 Tic Tac Toe board.
    0 = empty, 1 = us, -1 = opponent.
    """
    try:
        state = tuple(board[r][c] for r in range(N) for c in range(N))
        legal = _legal_moves_tuple(state)

        # Absolute fallback if board is full or malformed
        if not legal:
            for r in range(N):
                for c in range(N):
                    if board[r][c] == 0:
                        return (r, c)
            return (0, 0)

        # 1. Win immediately.
        mv = _immediate_move(state, 1)
        if mv is not None:
            return mv

        # 2. Block opponent's immediate win.
        mv = _immediate_move(state, -1)
        if mv is not None:
            return mv

        # 3. If we can create multiple immediate threats, do it.
        best_fork = None
        best_fork_score = 1
        for m in legal:
            fs = _creates_fork_score(state, m, 1)
            if fs > best_fork_score:
                best_fork_score = fs
                best_fork = m
        if best_fork is not None:
            return best_fork

        # 4. Block opponent fork if urgent.
        opp_best = None
        opp_best_score = 1
        for m in legal:
            fs = _creates_fork_score(state, m, -1)
            if fs > opp_best_score:
                opp_best_score = fs
                opp_best = m
        if opp_best is not None:
            return opp_best

        # 5. Alpha-beta search.
        best_val = -10**9
        best_move = legal[0]

        # Search promising moves first.
        candidates = []
        for r, c in legal:
            idx = r * N + c
            lst = list(state)
            lst[idx] = 1
            child = tuple(lst)
            candidates.append((_heuristic(child), r, c, child))
        candidates.sort(reverse=True, key=lambda x: x[0])

        for _, r, c, child in candidates:
            val = _minimax(child, -1, -10**9, 10**9)
            if val > best_val:
                best_val = val
                best_move = (r, c)

        # Ensure legality before return.
        br, bc = best_move
        if 0 <= br < N and 0 <= bc < N and board[br][bc] == 0:
            return best_move

        return legal[0]

    except Exception:
        # Last-resort safety: always return some empty cell if possible.
        for r in range(4):
            for c in range(4):
                try:
                    if board[r][c] == 0:
                        return (r, c)
                except Exception:
                    pass
        return (0, 0)
