
from typing import List, Tuple, Optional

def check_winner(board: List[List[int]]) -> Optional[int]:
    """Check if there's a winner. Returns 1 (me), -1 (opponent), or None."""
    # Check rows
    for row in board:
        if row[0] == row[1] == row[2] != 0:
            return row[0]
    # Check columns
    for col in range(3):
        if board[0][col] == board[1][col] == board[2][col] != 0:
            return board[0][col]
    # Check diagonals
    if board[0][0] == board[1][1] == board[2][2] != 0:
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] != 0:
        return board[0][2]
    return None

def is_draw(board: List[List[int]]) -> bool:
    """Check if the board is full (draw)."""
    return all(cell != 0 for row in board for cell in row)

def get_empty_cells(board: List[List[int]]) -> List[Tuple[int, int]]:
    """Return list of (row, col) tuples for empty cells."""
    return [(r, c) for r in range(3) for c in range(3) if board[r][c] == 0]

def minimax(board: List[List[int]], depth: int, is_maximizing: bool) -> int:
    """
    Minimax algorithm. Returns score from current player's perspective.
    Positive scores favor me (1), negative favor opponent (-1).
    """
    winner = check_winner(board)
    if winner == 1:
        return 10 - depth  # Prefer quicker wins
    elif winner == -1:
        return depth - 10  # Prefer slower losses
    elif is_draw(board):
        return 0
    
    if is_maximizing:
        max_eval = -float('inf')
        for r, c in get_empty_cells(board):
            board[r][c] = 1
            eval = minimax(board, depth + 1, False)
            board[r][c] = 0
            max_eval = max(max_eval, eval)
        return max_eval
    else:
        min_eval = float('inf')
        for r, c in get_empty_cells(board):
            board[r][c] = -1
            eval = minimax(board, depth + 1, True)
            board[r][c] = 0
            min_eval = min(min_eval, eval)
        return min_eval

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Determine the best move for the current board state.
    Returns (row, col) tuple.
    """
    empty_cells = get_empty_cells(board)
    
    # Safety check: if board is full (shouldn't happen in normal play)
    if not empty_cells:
        return (0, 0)
    
    # 1. Check for immediate winning move
    for r, c in empty_cells:
        board[r][c] = 1
        if check_winner(board) == 1:
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0
    
    # 2. Check for opponent's immediate winning move (must block)
    for r, c in empty_cells:
        board[r][c] = -1
        if check_winner(board) == -1:
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0
    
    # 3. Use minimax to find optimal move
    best_score = -float('inf')
    best_move = empty_cells[0]  # Default to first available
    
    for r, c in empty_cells:
        board[r][c] = 1
        score = minimax(board, 0, False)
        board[r][c] = 0
        if score > best_score:
            best_score = score
            best_move = (r, c)
    
    return best_move
