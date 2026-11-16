
from functools import lru_cache

# Preferred move order: center, corners, then edges.
_ORDER = (4, 0, 2, 6, 8, 1, 3, 5, 7)

# All winning lines on a 3x3 Tic Tac Toe board flattened to length 9.
_LINES = (
    (0, 1, 2),
    (3, 4, 5),
    (6, 7, 8),
    (0, 3, 6),
    (1, 4, 7),
    (2, 5, 8),
    (0, 4, 8),
    (2, 4, 6),
)


def _winner(state):
    """Return 1 if we have won, -1 if the opponent has won, else 0."""
    for a, b, c in _LINES:
        s = state[a] + state[b] + state[c]
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0


@lru_cache(maxsize=None)
def _solve(state, player):
    """
    Minimax value of the position from our perspective:
    +1 = forced win for us
     0 = forced draw
    -1 = forced loss for us

    'player' is the side to move in this simulated state: 1 or -1.
    """
    w = _winner(state)
    if w != 0:
        return w
    if 0 not in state:
        return 0

    if player == 1:
        best = -2
        for i in _ORDER:
            if state[i] != 0:
                continue
            nxt = list(state)
            nxt[i] = 1
            score = _solve(tuple(nxt), -1)
            if score > best:
                best = score
                if best == 1:
                    break
        return best
    else:
        best = 2
        for i in _ORDER:
            if state[i] != 0:
                continue
            nxt = list(state)
            nxt[i] = -1
            score = _solve(tuple(nxt), 1)
            if score < best:
                best = score
                if best == -1:
                    break
        return best


def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Choose a legal move (row, col) for a 3x3 Tic Tac Toe board where:
      0 = empty
      1 = our marks
     -1 = opponent marks
    """
    # Flatten board robustly into a 9-cell tuple.
    state_list = []
    for r in range(3):
        for c in range(3):
            try:
                v = board[r][c]
            except Exception:
                v = 1  # Treat malformed cells as occupied.
            if v == 0:
                state_list.append(0)
            elif v == 1:
                state_list.append(1)
            else:
                state_list.append(-1)
    state = tuple(state_list)

    legal_moves = [i for i in _ORDER if state[i] == 0]

    # If no legal moves exist, no legal return is possible; bounded fallback.
    if not legal_moves:
        return (0, 0)

    # If the board is already terminal or otherwise strange, just return a legal move.
    if _winner(state) != 0:
        return divmod(legal_moves[0], 3)

    # Choose the move with the best exact minimax value.
    best_move = legal_moves[0]
    best_score = -2

    for i in legal_moves:
        nxt = list(state)
        nxt[i] = 1
        score = _solve(tuple(nxt), -1)
        if score > best_score:
            best_score = score
            best_move = i
            if best_score == 1:
                break

    return divmod(best_move, 3)
