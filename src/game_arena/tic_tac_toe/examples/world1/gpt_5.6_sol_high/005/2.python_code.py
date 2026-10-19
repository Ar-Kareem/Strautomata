
from functools import lru_cache
from typing import List, Tuple


Board = Tuple[Tuple[int, ...], ...]
Move = Tuple[int, int]

_LINES = (
    ((0, 0), (0, 1), (0, 2)),
    ((1, 0), (1, 1), (1, 2)),
    ((2, 0), (2, 1), (2, 2)),
    ((0, 0), (1, 0), (2, 0)),
    ((0, 1), (1, 1), (2, 1)),
    ((0, 2), (1, 2), (2, 2)),
    ((0, 0), (1, 1), (2, 2)),
    ((0, 2), (1, 1), (2, 0)),
)

# Used only after minimax and exploitation scores are tied.
_MOVE_ORDER = (
    (1, 1),
    (0, 0),
    (0, 2),
    (2, 0),
    (2, 2),
    (0, 1),
    (1, 0),
    (1, 2),
    (2, 1),
)
_MOVE_PRIORITY = {
    move: len(_MOVE_ORDER) - index
    for index, move in enumerate(_MOVE_ORDER)
}


def _winner(board: Board) -> int:
    for line in _LINES:
        (a, b, c) = line
        value = board[a[0]][a[1]]
        if value != 0 and value == board[b[0]][b[1]] == board[c[0]][c[1]]:
            return value
    return 0


def _empty_cells(board: Board) -> Tuple[Move, ...]:
    return tuple(
        (row, col)
        for row in range(3)
        for col in range(3)
        if board[row][col] == 0
    )


def _play(board: Board, move: Move, player: int) -> Board:
    row, col = move
    updated = [list(line) for line in board]
    updated[row][col] = player
    return tuple(tuple(line) for line in updated)


@lru_cache(maxsize=None)
def _minimax(board: Board, turn: int) -> int:
    """
    Returns the perfect-play outcome from our perspective:
      1  = we can force a win
      0  = we can force at least a draw
     -1  = the opponent can force a win
    """
    winner = _winner(board)
    if winner != 0:
        return winner

    moves = _empty_cells(board)
    if not moves:
        return 0

    if turn == 1:
        best = -2
        for move in moves:
            value = _minimax(_play(board, move, 1), -1)
            if value > best:
                best = value
            if best == 1:
                break
        return best

    best = 2
    for move in moves:
        value = _minimax(_play(board, move, -1), 1)
        if value < best:
            best = value
        if best == -1:
            break
    return best


@lru_cache(maxsize=None)
def _exploit_score(board: Board, turn: int) -> Tuple[float, float]:
    """
    Secondary evaluation against an opponent modeled as choosing uniformly
    among legal moves.

    Our own simulated moves are restricted to minimax-optimal moves, so this
    score can improve exploitation of mistakes without sacrificing safety.

    The first component is expected game result. The second favors faster
    wins and slower losses.
    """
    winner = _winner(board)
    if winner != 0:
        remaining = len(_empty_cells(board))
        return float(winner), float(winner * remaining)

    moves = _empty_cells(board)
    if not moves:
        return 0.0, 0.0

    if turn == 1:
        required_value = _minimax(board, 1)
        best_score = (-float("inf"), -float("inf"))

        for move in moves:
            child = _play(board, move, 1)
            if _minimax(child, -1) == required_value:
                score = _exploit_score(child, -1)
                if score > best_score:
                    best_score = score

        return best_score

    total_result = 0.0
    total_speed = 0.0

    for move in moves:
        child = _play(board, move, -1)
        result, speed = _exploit_score(child, 1)
        total_result += result
        total_speed += speed

    count = float(len(moves))
    return total_result / count, total_speed / count


def policy(board: List[List[int]]) -> Tuple[int, int]:
    position: Board = tuple(
        tuple(int(board[row][col]) for col in range(3))
        for row in range(3)
    )

    legal_moves = _empty_cells(position)

    # The game engine should only call the policy when a move is available.
    # No legal return value exists for a completely full board.
    if not legal_moves:
        return (0, 0)

    best_game_value = -2
    candidates = []

    # First retain only moves with the best perfect-play outcome.
    for move in legal_moves:
        child = _play(position, move, 1)
        game_value = _minimax(child, -1)

        if game_value > best_game_value:
            best_game_value = game_value
            candidates = [(move, child)]
        elif game_value == best_game_value:
            candidates.append((move, child))

    # Among equally safe moves, maximize exploitation score and then use
    # deterministic positional preference.
    best_move = candidates[0][0]
    best_key = (-float("inf"), -float("inf"), -1)

    for move, child in candidates:
        expected_result, speed_score = _exploit_score(child, -1)
        key = (
            expected_result,
            speed_score,
            _MOVE_PRIORITY.get(move, 0),
        )

        if key > best_key:
            best_key = key
            best_move = move

    return best_move
