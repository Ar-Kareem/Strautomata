
from functools import lru_cache

# Preferred move order for tie-breaking and faster alpha-beta style pruning effect.
PREFERRED_MOVES = [
    (1, 1),  # center
    (0, 0), (0, 2), (2, 0), (2, 2),  # corners
    (0, 1), (1, 0), (1, 2), (2, 1),  # edges
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


def _winner(flat_board):
    for line in WIN_LINES:
        s = sum(flat_board[r * 3 + c] for r, c in line)
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0


def _legal_moves(flat_board):
    moves = []
    for r, c in PREFERRED_MOVES:
        if flat_board[r * 3 + c] == 0:
            moves.append((r, c))
    return moves


@lru_cache(maxsize=None)
def _solve(flat_board, turn):
    """
    Returns (result, distance):
      result in {-1, 0, 1} from player 1's perspective
      distance = plies to terminal under optimal play
    turn is 1 or -1, indicating whose move it is.
    """
    w = _winner(flat_board)
    if w != 0:
        return (w, 0)

    moves = _legal_moves(flat_board)
    if not moves:
        return (0, 0)

    if turn == 1:
        # Maximize result for player 1; among equals, prefer faster wins / slower losses.
        best_result = -2
        best_dist = 10**9
        for r, c in moves:
            idx = r * 3 + c
            new_board = list(flat_board)
            new_board[idx] = 1
            child_result, child_dist = _solve(tuple(new_board), -1)
            total_dist = child_dist + 1

            if child_result > best_result:
                best_result = child_result
                best_dist = total_dist
            elif child_result == best_result:
                if best_result == 1:
                    # Faster win
                    if total_dist < best_dist:
                        best_dist = total_dist
                elif best_result == -1:
                    # Slower loss
                    if total_dist > best_dist:
                        best_dist = total_dist
                else:
                    # Any draw; prefer shorter line slightly
                    if total_dist < best_dist:
                        best_dist = total_dist
        return (best_result, best_dist)

    else:
        # Minimize result for player 1; among equals, prefer faster wins for -1 / slower losses for -1.
        best_result = 2
        best_dist = 10**9
        for r, c in moves:
            idx = r * 3 + c
            new_board = list(flat_board)
            new_board[idx] = -1
            child_result, child_dist = _solve(tuple(new_board), 1)
            total_dist = child_dist + 1

            if child_result < best_result:
                best_result = child_result
                best_dist = total_dist
            elif child_result == best_result:
                if best_result == -1:
                    # Faster win for player -1
                    if total_dist < best_dist:
                        best_dist = total_dist
                elif best_result == 1:
                    # Slower loss for player -1
                    if total_dist > best_dist:
                        best_dist = total_dist
                else:
                    if total_dist < best_dist:
                        best_dist = total_dist
        return (best_result, best_dist)


def policy(board: list[list[int]]) -> tuple[int, int]:
    # Flatten board safely.
    flat = tuple(board[r][c] for r in range(3) for c in range(3))
    moves = _legal_moves(flat)

    # Always return a legal move if one exists.
    if not moves:
        return (0, 0)

    # If we can win immediately, do it.
    for r, c in moves:
        idx = r * 3 + c
        new_board = list(flat)
        new_board[idx] = 1
        if _winner(tuple(new_board)) == 1:
            return (r, c)

    # If opponent could win next turn, block it if possible.
    opponent_winning_squares = set()
    for r, c in moves:
        idx = r * 3 + c
        new_board = list(flat)
        new_board[idx] = -1
        if _winner(tuple(new_board)) == -1:
            opponent_winning_squares.add((r, c))
    if opponent_winning_squares:
        for mv in PREFERRED_MOVES:
            if mv in opponent_winning_squares and mv in moves:
                return mv

    # Full minimax search for optimal move.
    best_move = moves[0]
    best_result = -2
    best_dist = 10**9

    for r, c in moves:
        idx = r * 3 + c
        new_board = list(flat)
        new_board[idx] = 1
        child_result, child_dist = _solve(tuple(new_board), -1)
        total_dist = child_dist + 1

        if child_result > best_result:
            best_result = child_result
            best_dist = total_dist
            best_move = (r, c)
        elif child_result == best_result:
            if best_result == 1:
                if total_dist < best_dist:
                    best_dist = total_dist
                    best_move = (r, c)
            elif best_result == -1:
                if total_dist > best_dist:
                    best_dist = total_dist
                    best_move = (r, c)
            else:
                if total_dist < best_dist:
                    best_dist = total_dist
                    best_move = (r, c)

    return best_move
