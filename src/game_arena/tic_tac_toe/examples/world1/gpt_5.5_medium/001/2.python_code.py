
from functools import lru_cache

# Preferred move order: center, corners, edges.
# This makes the policy choose strong human-like moves among equally optimal options.
MOVE_ORDER = (
    (1, 1),
    (0, 0), (0, 2), (2, 0), (2, 2),
    (0, 1), (1, 0), (1, 2), (2, 1),
)


def _winner_tuple(state):
    """Return 1 if we win, -1 if opponent wins, 0 otherwise."""
    lines = (
        (0, 1, 2),
        (3, 4, 5),
        (6, 7, 8),
        (0, 3, 6),
        (1, 4, 7),
        (2, 5, 8),
        (0, 4, 8),
        (2, 4, 6),
    )

    for a, b, c in lines:
        s = state[a] + state[b] + state[c]
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0


def _is_full(state):
    return all(x != 0 for x in state)


@lru_cache(maxsize=None)
def _minimax(state, turn, depth, alpha, beta):
    """
    Minimax score from this state.
    turn == 1 means our turn, maximizing.
    turn == -1 means opponent turn, minimizing.
    """
    w = _winner_tuple(state)
    if w == 1:
        return 100 - depth
    if w == -1:
        return depth - 100
    if _is_full(state):
        return 0

    if turn == 1:
        best = -10_000
        for r, c in MOVE_ORDER:
            idx = 3 * r + c
            if state[idx] == 0:
                nxt = list(state)
                nxt[idx] = 1
                score = _minimax(tuple(nxt), -1, depth + 1, alpha, beta)
                if score > best:
                    best = score
                if best > alpha:
                    alpha = best
                if beta <= alpha:
                    break
        return best
    else:
        best = 10_000
        for r, c in MOVE_ORDER:
            idx = 3 * r + c
            if state[idx] == 0:
                nxt = list(state)
                nxt[idx] = -1
                score = _minimax(tuple(nxt), 1, depth + 1, alpha, beta)
                if score < best:
                    best = score
                if best < beta:
                    beta = best
                if beta <= alpha:
                    break
        return best


def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Return the best legal move for player 1 on a 3x3 Tic Tac Toe board.

    board values:
      0  = empty
      1  = our mark
      -1 = opponent mark
    """
    state = tuple(board[r][c] for r in range(3) for c in range(3))

    # Safety fallback list of legal moves.
    legal_moves = [(r, c) for r, c in MOVE_ORDER if board[r][c] == 0]

    # If somehow called with no legal moves, return a valid-shaped tuple.
    # In normal play this branch should never be reached.
    if not legal_moves:
        return (0, 0)

    # Immediate winning move if available.
    for r, c in legal_moves:
        idx = 3 * r + c
        nxt = list(state)
        nxt[idx] = 1
        if _winner_tuple(tuple(nxt)) == 1:
            return (r, c)

    # Immediate block if opponent can win next move.
    for r, c in legal_moves:
        idx = 3 * r + c
        nxt = list(state)
        nxt[idx] = -1
        if _winner_tuple(tuple(nxt)) == -1:
            return (r, c)

    # Full minimax search.
    best_move = legal_moves[0]
    best_score = -10_000

    for r, c in legal_moves:
        idx = 3 * r + c
        nxt = list(state)
        nxt[idx] = 1
        score = _minimax(tuple(nxt), -1, 1, -10_000, 10_000)

        if score > best_score:
            best_score = score
            best_move = (r, c)

    return best_move
