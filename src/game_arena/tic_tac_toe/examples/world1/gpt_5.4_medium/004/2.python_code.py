
from functools import lru_cache
from typing import List, Tuple

# Preferred move order for tie-breaking among equally good moves:
# center, corners, then edges.
MOVE_ORDER = [
    (1, 1),
    (0, 0), (0, 2), (2, 0), (2, 2),
    (0, 1), (1, 0), (1, 2), (2, 1),
]

WIN_LINES = [
    ((0, 0), (0, 1), (0, 2)),
    ((1, 0), (1, 1), (1, 2)),
    ((2, 0), (2, 1), (2, 2)),
    ((0, 0), (1, 0), (2, 0)),
    ((0, 1), (1, 1), (2, 1)),
    ((0, 2), (1, 2), (2, 2)),
    ((0, 0), (1, 1), (2, 2)),
    ((0, 2), (1, 1), (2, 0)),
]


def _winner(state: Tuple[Tuple[int, int, int], Tuple[int, int, int], Tuple[int, int, int]]) -> int:
    for line in WIN_LINES:
        s = sum(state[r][c] for r, c in line)
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0


def _is_full(state: Tuple[Tuple[int, int, int], Tuple[int, int, int], Tuple[int, int, int]]) -> bool:
    for row in state:
        for cell in row:
            if cell == 0:
                return False
    return True


def _ordered_moves(state: Tuple[Tuple[int, int, int], Tuple[int, int, int], Tuple[int, int, int]]):
    return [(r, c) for (r, c) in MOVE_ORDER if state[r][c] == 0]


def _play(
    state: Tuple[Tuple[int, int, int], Tuple[int, int, int], Tuple[int, int, int]],
    move: Tuple[int, int],
    player: int,
) -> Tuple[Tuple[int, int, int], Tuple[int, int, int], Tuple[int, int, int]]:
    r, c = move
    new_rows = [list(row) for row in state]
    new_rows[r][c] = player
    return tuple(tuple(row) for row in new_rows)


@lru_cache(maxsize=None)
def _minimax(
    state: Tuple[Tuple[int, int, int], Tuple[int, int, int], Tuple[int, int, int]],
    player: int,
    depth: int,
) -> int:
    """
    Returns score from our perspective (player 1 is us).
    Higher is better for us.
    """
    w = _winner(state)
    if w == 1:
        return 10 - depth
    if w == -1:
        return depth - 10
    if _is_full(state):
        return 0

    moves = _ordered_moves(state)

    if player == 1:
        best = -10**9
        for mv in moves:
            score = _minimax(_play(state, mv, 1), -1, depth + 1)
            if score > best:
                best = score
        return best
    else:
        best = 10**9
        for mv in moves:
            score = _minimax(_play(state, mv, -1), 1, depth + 1)
            if score < best:
                best = score
        return best


def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Choose a legal move for 3x3 Tic Tac Toe.
    board[r][c] values:
      0  = empty
      1  = our mark
     -1  = opponent mark
    """
    state = tuple(tuple(int(cell) for cell in row) for row in board)

    legal_moves = _ordered_moves(state)
    if legal_moves:
        # 1) Immediate winning move
        for mv in legal_moves:
            next_state = _play(state, mv, 1)
            if _winner(next_state) == 1:
                return mv

        # 2) Immediate block if opponent has a winning move next
        opp_wins = set()
        for mv in legal_moves:
            opp_state = _play(state, mv, -1)
            if _winner(opp_state) == -1:
                opp_wins.add(mv)
        if opp_wins:
            for mv in legal_moves:
                if mv in opp_wins:
                    return mv

        # 3) Full minimax
        best_score = -10**9
        best_move = legal_moves[0]
        for mv in legal_moves:
            score = _minimax(_play(state, mv, 1), -1, 1)
            if score > best_score:
                best_score = score
                best_move = mv
        return best_move

    # Fallback: no legal moves. This should not happen in a valid arena call.
    return (0, 0)
