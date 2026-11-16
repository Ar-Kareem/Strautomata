
from functools import lru_cache

# Preferred move order: center, corners, then edges.
MOVE_ORDER = (4, 0, 2, 6, 8, 1, 3, 5, 7)
MOVE_RANK = {idx: rank for rank, idx in enumerate(MOVE_ORDER)}

# Winning lines on a flattened 3x3 board.
LINES = (
    (0, 1, 2),
    (3, 4, 5),
    (6, 7, 8),
    (0, 3, 6),
    (1, 4, 7),
    (2, 5, 8),
    (0, 4, 8),
    (2, 4, 6),
)


def _winner(state: tuple[int, ...]) -> int:
    """Return 1 if player 1 has won, -1 if player -1 has won, else 0."""
    for a, b, c in LINES:
        s = state[a] + state[b] + state[c]
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0


def _better_candidate(
    res: int,
    dist: int,
    idx: int,
    best_res: int,
    best_dist: int,
    best_idx: int,
) -> bool:
    """
    Compare two candidate moves.

    res:
      1  -> current player can force a win
      0  -> current player can force a draw
     -1  -> current player will lose with perfect play

    dist:
      number of plies to game end under optimal continuation
    """
    if res != best_res:
        return res > best_res

    # Prefer faster wins.
    if res == 1 and dist != best_dist:
        return dist < best_dist

    # Prefer slower losses.
    if res == -1 and dist != best_dist:
        return dist > best_dist

    # For equal outcomes, prefer stronger board positions.
    return MOVE_RANK[idx] < MOVE_RANK[best_idx]


@lru_cache(maxsize=None)
def _solve(state: tuple[int, ...], to_move: int) -> tuple[int, int]:
    """
    Solve the position from the perspective of 'to_move'.

    Returns (result, distance):
      result = 1  if 'to_move' can force a win
      result = 0  if 'to_move' can force a draw
      result = -1 if 'to_move' will lose with perfect play
    """
    w = _winner(state)
    if w != 0:
        # If the game is already won on this board, the player to move has lost:
        # the previous player made the winning move.
        return (-1, 0)

    if 0 not in state:
        return (0, 0)

    best_res = -2
    best_dist = 10
    best_idx = MOVE_ORDER[-1]

    for idx in MOVE_ORDER:
        if state[idx] != 0:
            continue

        child = state[:idx] + (to_move,) + state[idx + 1 :]
        opp_res, opp_dist = _solve(child, -to_move)

        # Opponent's result becomes our negated result.
        cur_res = -opp_res
        cur_dist = opp_dist + 1

        if best_res == -2 or _better_candidate(
            cur_res, cur_dist, idx, best_res, best_dist, best_idx
        ):
            best_res = cur_res
            best_dist = cur_dist
            best_idx = idx

    return (best_res, best_dist)


def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Choose a legal move for a 3x3 Tic Tac Toe board.

    board[r][c]:
      0  = empty
      1  = our mark
     -1  = opponent mark
    """
    state = tuple(board[r][c] for r in range(3) for c in range(3))

    legal = [idx for idx in MOVE_ORDER if state[idx] == 0]
    if not legal:
        # No legal move exists; this should not happen in a valid arena call.
        return (0, 0)

    # Safety fallback for already-terminal or malformed states:
    # still return a legal empty cell if one exists.
    if _winner(state) != 0:
        idx = legal[0]
        return (idx // 3, idx % 3)

    best_res = -2
    best_dist = 10
    best_idx = legal[0]

    for idx in legal:
        child = state[:idx] + (1,) + state[idx + 1 :]
        opp_res, opp_dist = _solve(child, -1)

        cur_res = -opp_res
        cur_dist = opp_dist + 1

        if best_res == -2 or _better_candidate(
            cur_res, cur_dist, idx, best_res, best_dist, best_idx
        ):
            best_res = cur_res
            best_dist = cur_dist
            best_idx = idx

    return (best_idx // 3, best_idx % 3)
