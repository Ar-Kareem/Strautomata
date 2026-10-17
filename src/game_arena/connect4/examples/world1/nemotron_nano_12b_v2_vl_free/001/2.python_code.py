
import numpy as np

def find_row(board, col):
    """Find the lowest empty row in the given column."""
    for r in range(5, -1, -1):
        if board[r][col] == 0:
            return r
    return 6  # Column is full

def has_win(board, player):
    """Check if the player has four in a row (win condition)."""
    # Vertical check
    for c in range(7):
        for r in range(3):
            if (board[r][c] == player and
                board[r+1][c] == player and board[r+2][c] == player and
                board[r+3][c] == player):
                return True
    # Horizontal check
    for r in range(6):
        for c in range(4):
            if (board[r][c] == player and
                board[r][c+1] == player and board[r][c+2] == player and
                board[r][c+3] == player):
                return True
    # Diagonal down-right check
    for r in range(3):
        for c in range(4):
            if (board[r][c] == player and
                board[r+1][c+1] == player and board[r+2][c+2] == player and
                board[r+3][c+3] == player):
                return True
    # Diagonal down-left check
    for r in range(3):
        for c in range(3, 7):
            if (board[r][c] == player and
                board[r+1][c-1] == player and board[r+2][c-2] == player and
                board[r+3][c-3] == player):
                return True
    return False

def policy(board: list[list[int]]) -> int:
    # Helper functions are defined within policy to encapsulate scope
    
    possible_columns = []
    for c in range(7):
        if find_row(board, c) != 6:
            possible_columns.append(c)
    
    # Step 1: Check for immediate win
    for c in possible_columns:
        temp_board = [row.copy() for row in board]
        row = find_row(temp_board, c)
        temp_board[row][c] = 1  # Place current player's disc
        if has_win(temp_board, 1):
            return c
    
    # Step 2: Find safe columns (opponent can't win next turn)
    safe_columns = []
    priority_order = [3, 2, 4, 1, 5, 0, 6]  # Center to edges priority
    for c in possible_columns:
        temp_board = [row.copy() for row in board]
        row = find_row(temp_board, c)
        temp_board[row][c] = 1  # Place our disc
        
        opponent_can_win = False
        # Check all opponent's possible moves in the new board state
        for d in range(7):
            if find_row(temp_board, d) != 6:
                temp2_board = [row.copy() for row in temp_board]
                rowo = find_row(temp2_board, d)
                temp2_board[rowo][d] = -1  # Simulate opponent's move
                if has_win(temp2_board, -1):
                    opponent_can_win = True
                    break
        
        if not opponent_can_win:
            safe_columns.append(c)
    
    # Step 3: Choose the highest-priority safe column
    if safe_columns:
        sorted_columns = sorted(safe_columns, key=lambda x: priority_order.index(x))
        return sorted_columns[0]
    
    # Step 4: If all moves allow opponent's immediate win, pick any column
    return possible_columns[0]
