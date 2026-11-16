
from typing import List, Tuple
import copy
from collections import defaultdict

# Constants for evaluation scores
WIN_SCORE = 10
LOSS_SCORE = -10
DRAW_SCORE = 0

def evaluate(board: List[List[int]]) -> int:
    """Return +WIN_SCORE, -LOSS_SCORE or DRAW_SCORE based on the terminal state."""
    # Check rows
    for row in board:
        if row[0] == row[1] == row[2] != 0:
            return WIN_SCORE if row[0] == 1 else LOSS_SCORE
    # Check columns
    for col in range(3):
        if board[0][col] == board[1][col] == board[2][col] != 0:
            return WIN_SCORE if board[0][col] == 1 else LOSS_SCORE
    # Check diagonals
    if board[0][0] == board[1][1] == board[2][2] != 0:
        return WIN_SCORE if board[0][0] == 1 else LOSS_SCORE
    if board[0][2] == board[1][1] == board[2][0] != 0:
        return WIN_SCORE if board[0][2] == 1 else LOSS_SCORE
    # Draw or ongoing
    if not any(cell == 0 for row in board for cell in row):
        return DRAW_SCORE
    return 0  # ongoing game

def is_win(board: List[List[int]], player: int) -> bool:
    """Return True if `player` (1 or -1) has a three‑in‑a‑row."""
    # Rows
    for row in board:
        if row[0] == row[1] == row[2] == player:
            return True
    # Columns
    for col in range(3):
        if board[0][col] == board[1][col] == board[2][col] == player:
            return True
    # Diagonals
    if board[0][0] == board[1][1] == board[2][2] == player:
        return True
    if board[0][2] == board[1][1] == board[2][0] == player:
        return True
    return False

def is_blockable(board: List[List[int]], opponent: int) -> Tuple[int, int] | None:
    """If opponent can win in one move, return the (row, col) that blocks them."""
    for i, j in [(0,0),(0,1),(0,2),
                (1,0),(1,1),(1,2),
                (2,0),(2,1),(2,2)]:
        if board[i][j] != 0:
            continue
        temp = copy.deepcopy(board)
        temp[i][j] = opponent
        if is_win(temp, opponent):
            return i, j
    return None

def heuristic_heuristic(board: List[List[int]]) -> Tuple[int, int] | None:
    """Apply simple heuristic preferences (center, corners, edges)."""
    # 1. Center
    if board[1][1] == 0:
        return 1, 1
    # 2. Corners
    for row, col in [(0,0),(0,2),(2,0),(2,2)]:
        if board[row][col] == 0:
            return row, col
    # 3. Edges
    for row, col in [(0,1),(1,0),(1,2),(2,1)]:
        if board[row][col] == 0:
            return row, col
    return None

# Simple cache to avoid re‑evaluating identical board states
# Key is a tuple of 9 ints (flattened), value is the minimax score
_cache: dict[Tuple[int, ...], int] = defaultdict(int)

def minimax(board: List[List[int]], depth: int, maximizing_player: bool,
           alpha: int, beta: int) -> int:
    """Alpha‑beta minimax with caching. Returns the optimal score."""
    key = tuple(board[i][j] for i in range(3) for j in range(3))
    if key in _cache:
        return _cache[key]

    result = evaluate(board)
    if result != 0:   # terminal state
        _cache[key] = result
        return result

    if maximizing_player:   # our turn (1)
        max_eval = LOSS_SCORE
        for i, j in [(r, c) for r in range(3) for c in range(3) if board[r][c] == 0]:
            new_board = copy.deepcopy(board)
            new_board[i][j] = 1
            eval = minimax(new_board, depth + 1, False, alpha, beta)
            alpha = max(alpha, eval)
            max_eval = max(max_eval, eval)
            if beta <= alpha:
                break
        _cache[key] = max_eval
        return max_eval
    else:   # opponent turn (-1)
        min_eval = WIN_SCORE
        for i, j in [(r, c) for r in range(3) for c in range(3) if board[r][c] == 0]:
            new_board = copy.deepcopy(board)
            new_board[i][j] = -1
            eval = minimax(new_board, depth + 1, True, alpha, beta)
            beta = min(beta, eval)
            min_eval = min(min_eval, eval)
            if beta <= alpha:
                break
        _cache[key] = min_eval
        return min_eval

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Return a legal move (row, col) for the current board state.
    The board uses: 1 = our mark, -1 = opponent's mark, 0 = empty.
    """
    # 1. Immediate win
    for i, j in [(r, c) for r in range(3) for c in range(3) if board[r][c] == 0]:
        if is_win([copy.deepcopy(board)[r][c] for r in range(3)], 1):
            return i, j

    # 2. Block opponent if they can win in the next move
    blocker = is_blockable(board, -1)
    if blocker is not None:
        return blocker

    # 3. Apply simple heuristic preferences
    heuristic_move = heuristic_heuristic(board)
    if heuristic_move:
        return heuristic_move

    # 4. Full minimax fallback
    # Collect all legal moves and compute their minimax values
    moves = [(r, c) for r in range(3) for c in range(3) if board[r][c] == 0]
    best_move = None
    best_score = LOSS_SCORE
    alpha, beta = -WIN_SCORE, WIN_SCORE

    for r, c in moves:
        new_board = copy.deepcopy(board)
        new_board[r][c] = 1
        score = minimax(new_board, 0, False, alpha, beta)   # opponent's turn
        if score > best_score:
            best_score = score
            best_move = (r, c)
        alpha = max(alpha, score)
        if alpha >= WIN_SCORE:
            break  # cannot do better

    # Fallback if for some reason no move was found (board full)
    if best_move is None:
        # This should never happen, but returning (0,0) satisfies type requirements.
        return (0, 0)
    return best_move
