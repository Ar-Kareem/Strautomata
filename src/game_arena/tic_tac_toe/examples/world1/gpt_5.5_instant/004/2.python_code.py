
from functools import lru_cache

WIN_LINES = (
    ((0, 0), (0, 1), (0, 2)),
    ((1, 0), (1, 1), (1, 2)),
    ((2, 0), (2, 1), (2, 2)),
    ((0, 0), (1, 0), (2, 0)),
    ((0, 1), (1, 1), (2, 1)),
    ((0, 2), (1, 2), (2, 2)),
    ((0, 0), (1, 1), (2, 2)),
    ((0, 2), (1, 1), (2, 0)),
)

# Move ordering improves alpha-beta pruning and also gives good tie-breaking.
ORDERED_MOVES = (
    (1, 1),
    (0, 0), (0, 2), (2, 0), (2, 2),
    (0, 1), (1, 0), (1, 2), (2, 1),
)


def _flatten(board):
    return tuple(board[r][c] for r in range(3) for c in range(3))


def _winner(state):
    for line in WIN_LINES:
        s = state[line[0][0] * 3 + line[0][1]] + state[line[1][0] * 3 + line[1][1]] + state[line[2][0] * 3 + line[2][1]]
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0


def _legal_moves(state):
    return [(r, c) for (r, c) in ORDERED_MOVES if state[r * 3 + c] == 0]


def _side_to_move(state):
    ones = state.count(1)
    negs = state.count(-1)
    # We are player 1. In normal play, if counts are equal, player 1 moves;
    # otherwise player -1 moves. This also handles most arena states robustly.
    return 1 if ones <= negs else -1


@lru_cache(maxsize=None)
def _minimax(state, side, alpha, beta):
    w = _winner(state)
    if w != 0:
        # Positive is good for player 1. Fewer empty cells means later terminal.
        # This formulation rewards faster wins and slower losses.
        empties = state.count(0)
        return w * (10 + empties)

    moves = _legal_moves(state)
    if not moves:
        return 0

    if side == 1:
        best = -100
        for r, c in moves:
            idx = r * 3 + c
            nxt = list(state)
            nxt[idx] = 1
            score = _minimax(tuple(nxt), -1, alpha, beta)
            if score > best:
                best = score
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        return best
    else:
        best = 100
        for r, c in moves:
            idx = r * 3 + c
            nxt = list(state)
            nxt[idx] = -1
            score = _minimax(tuple(nxt), 1, alpha, beta)
            if score < best:
                best = score
            if best < beta:
                beta = best
            if alpha >= beta:
                break
        return best


def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Return a legal move for player 1 on a 3x3 Tic Tac Toe board.
    Board values: 0 empty, 1 us, -1 opponent.
    """
    try:
        state = _flatten(board)
        legal = _legal_moves(state)
        if not legal:
            # No legal move exists, but the API requires a tuple. This should not
            # occur during a valid game.
            return (0, 0)

        # Immediate tactical checks are not necessary for correctness, but provide
        # clear and fast handling.
        for r, c in legal:
            idx = r * 3 + c
            nxt = list(state)
            nxt[idx] = 1
            if _winner(tuple(nxt)) == 1:
                return (r, c)

        for r, c in legal:
            idx = r * 3 + c
            nxt = list(state)
            nxt[idx] = -1
            if _winner(tuple(nxt)) == -1:
                return (r, c)

        # Determine whose turn the board implies. The policy is normally called
        # only when player 1 is to move, but if the board is irregular, still
        # select the best legal move for player 1.
        side = _side_to_move(state)
        if side != 1:
            side = 1

        best_move = legal[0]
        best_score = -100

        for r, c in legal:
            idx = r * 3 + c
            nxt = list(state)
            nxt[idx] = 1
            score = _minimax(tuple(nxt), -1, -100, 100)

            # Tie-break using ORDERED_MOVES implicitly by only replacing on >
            if score > best_score:
                best_score = score
                best_move = (r, c)

        return best_move

    except Exception:
        # Absolute safety fallback: return the first empty cell in row-major order.
        for r in range(3):
            for c in range(3):
                try:
                    if board[r][c] == 0:
                        return (r, c)
                except Exception:
                    pass
        return (0, 0)
