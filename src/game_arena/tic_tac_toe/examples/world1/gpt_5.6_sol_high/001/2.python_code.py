
from functools import lru_cache


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

# Used only as a final tie-breaker.
_MOVE_ORDER = (
    (1, 1),
    (0, 0), (0, 2), (2, 0), (2, 2),
    (0, 1), (1, 0), (1, 2), (2, 1),
)


def _winner(state: tuple[tuple[int, ...], ...]) -> int:
    for line in _LINES:
        (r1, c1), (r2, c2), (r3, c3) = line
        value = state[r1][c1]
        if value != 0 and value == state[r2][c2] == state[r3][c3]:
            return value
    return 0


def policy(board: list[list[int]]) -> tuple[int, int]:
    state = tuple(tuple(int(cell) for cell in row) for row in board)
    legal_moves = [move for move in _MOVE_ORDER if state[move[0]][move[1]] == 0]

    # A legal move cannot exist on a full board; normal game engines do not
    # request a policy action in that state.
    if not legal_moves:
        return (0, 0)

    @lru_cache(maxsize=None)
    def solve(
        position: tuple[tuple[int, ...], ...],
        turn: int,
    ) -> tuple[int, float]:
        """
        Return:
          worst_case: minimax score against perfect opposition
          expectation: score against uniformly random opponent moves

        The policy optimizes worst_case first, preserving perfect-play safety.
        """
        winner = _winner(position)
        empty_count = sum(cell == 0 for row in position for cell in row)

        if winner != 0:
            # More remaining cells means the result happened sooner.
            score = winner * (10 + empty_count)
            return score, float(score)

        if empty_count == 0:
            return 0, 0.0

        moves = [
            move for move in _MOVE_ORDER
            if position[move[0]][move[1]] == 0
        ]

        child_values = []
        for row, col in moves:
            mutable = [list(r) for r in position]
            mutable[row][col] = turn
            child = tuple(tuple(r) for r in mutable)
            child_values.append(solve(child, -turn))

        if turn == 1:
            # Never trade away a better guaranteed result. If several moves
            # have the same minimax result, exploit likely opponent mistakes.
            best_worst = max(value[0] for value in child_values)
            best_expectation = max(
                value[1]
                for value in child_values
                if value[0] == best_worst
            )
            return best_worst, best_expectation

        # For worst-case analysis, the opponent selects the most damaging move.
        # For secondary analysis, model the opponent as choosing legal moves
        # uniformly at random.
        worst_case = min(value[0] for value in child_values)
        expectation = sum(value[1] for value in child_values) / len(child_values)
        return worst_case, expectation

    best_move = legal_moves[0]
    best_value = None

    for row, col in legal_moves:
        mutable = [list(r) for r in state]
        mutable[row][col] = 1
        child = tuple(tuple(r) for r in mutable)
        value = solve(child, -1)

        if best_value is None or value > best_value:
            best_value = value
            best_move = (row, col)

    return best_move
