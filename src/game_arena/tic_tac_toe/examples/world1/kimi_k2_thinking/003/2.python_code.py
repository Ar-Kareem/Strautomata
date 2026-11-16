
import math

def _empty_cells(board):
    """Return a list of (row, col) tuples that are empty."""
    return [(r, c) for r in range(3) for c in range(3) if board[r][c] == 0]

def _has_win(board, player):
    """Check if `player` (1 or -1) has a winning line."""
    # rows and columns
    for i in range(3):
        if all(board[i][j] == player for j in range(3)):
            return True
        if all(board[j][i] == player for j in range(3)):
            return True
    # diagonals
    if board[0][0] == player and board[1][1] == player and board[2][2] == player:
        return True
    if board[0][2] == player and board[1][1] == player and board[2][0] == player:
        return True
    return False

def _evaluate(board):
    """Return 1 if X wins, -1 if O wins, 0 otherwise."""
    if _has_win(board, 1):
        return 1
    if _has_win(board, -1):
        return -1
    return 0

def _is_full(board):
    """True iff the board has no empty cells."""
    return all(cell != 0 for row in board for cell in row)

def _minimax(board, alpha, beta, maximizing):
    """Alpha‑beta minimax. Returns the score of the best continuation."""
    score = _evaluate(board)
    if score != 0:               # someone already won
        return score
    if _is_full(board):          # draw
        return 0

    if maximizing:               # Player 1 (us)
        max_eval = -math.inf
        for r, c in _empty_cells(board):
            board[r][c] = 1
            eval_ = _minimax(board, alpha, beta, False)
            board[r][c] = 0
            max_eval = max(max_eval, eval_)
            alpha = max(alpha, eval_)
            if beta <= alpha:
                break
        return max_eval
    else:                        # Player -1 (opponent)
        min_eval = math.inf
        for r, c in _empty_cells(board):
            board[r][c] = -1
            eval_ = _minimax(board, alpha, beta, True)
            board[r][c] = 0
            min_eval = min(min_eval, eval_)
            beta = min(beta, eval_)
            if beta <= alpha:
                break
        return min_eval

def _best_move(board):
    """Return the optimal (row, col) for the current board."""
    empty = _empty_cells(board)
    if not empty:                     # Should never happen, but keep legal
        return (0, 0)

    best_score = -math.inf
    candidates = []

    for r, c in empty:
        board[r][c] = 1
        score = _minimax(board, -math.inf, math.inf, False)
        board[r][c] = 0
        if score > best_score:
            best_score = score
            candidates = [(r, c)]
        elif score == best_score:
            candidates.append((r, c))

    # Tie‑break: centre > corners > edges
    priority = {
        (1, 1): 0,
        (0, 0): 1, (0, 2): 1, (2, 0): 1, (2, 2): 1,
        (0, 1): 2, (1, 0): 2, (1, 2): 2, (2, 1): 2,
    }
    candidates.sort(key=lambda x: priority[x])
    return candidates[0]

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Return the next move for player 1 on a 3×3 Tic‑Tac‑Toe board.

    The board is a list of three lists, each containing 0 (empty), 1 (our mark)
    or -1 (opponent's mark). The returned tuple (row, col) is guaranteed to be
    a legal empty cell.
    """
    # Work on a copy to avoid mutating the caller's board
    board_copy = [row[:] for row in board]
    return _best_move(board_copy)
