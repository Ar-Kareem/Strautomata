
from typing import Optional


def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Optimal Tic Tac Toe policy using the minimax algorithm.
    Returns a tuple (row, col) representing the best legal move.
    Guarantees to never lose against any opponent.
    """
    empty_cells = [(r, c) for r in range(3) for c in range(3) if board[r][c] == 0]
    
    if not empty_cells:
        return (0, 0)
    
    best_move = empty_cells[0]
    best_score = float('-inf')
    
    for r, c in empty_cells:
        board[r][c] = 1
        score = _minimax(board, False)
        board[r][c] = 0
        
        if score > best_score:
            best_score = score
            best_move = (r, c)
    
    return best_move


def _minimax(board: list[list[int]], is_maximizing: bool) -> int:
    """
    Minimax algorithm helper.
    Returns: 1 for win, -1 for loss, 0 for draw.
    """
    winner = _check_winner(board)
    if winner is not None:
        return winner
    
    if is_maximizing:
        best_score = float('-inf')
        for r in range(3):
            for c in range(3):
                if board[r][c] == 0:
                    board[r][c] = 1
                    score = _minimax(board, False)
                    board[r][c] = 0
                    best_score = max(best_score, score)
        return best_score
    else:
        best_score = float('inf')
        for r in range(3):
            for c in range(3):
                if board[r][c] == 0:
                    board[r][c] = -1
                    score = _minimax(board, True)
                    board[r][c] = 0
                    best_score = min(best_score, score)
        return best_score


def _check_winner(board: list[list[int]]) -> Optional[int]:
    """
    Check for winner or draw.
    Returns: 1 (player 1 wins), -1 (player -1 wins), 0 (draw), None (ongoing).
    """
    # Check rows
    for r in range(3):
        if board[r][0] == board[r][1] == board[r][2] != 0:
            return board[r][0]
    
    # Check columns
    for c in range(3):
        if board[0][c] == board[1][c] == board[2][c] != 0:
            return board[0][c]
    
    # Check diagonals
    if board[0][0] == board[1][1] == board[2][2] != 0:
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] != 0:
        return board[0][2]
    
    # Check if game continues
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                return None
    
    return 0  # Draw
