
import numpy as np

def is_winning_move(board: list[list[int]], col: int, player: int) -> bool:
    # Temporary drop the player's piece in the column
    row = next((r for r in range(6) if board[r][col] == 0), None)
    if row is None:
        return False  # Column is full
    
    board[row][col] = player  # Place the piece

    # Check for horizontal, vertical, and diagonal wins
    for dr, dc in [(0, 1), (1, 0), (1, 1), (1, -1)]:
        count = 1
        # Count in the positive direction
        for step in range(1, 4):
            r, c = row + step * dr, col + step * dc
            if 0 <= r < 6 and 0 <= c < 7 and board[r][c] == player:
                count += 1
            else:
                break
        
        # Count in the negative direction
        for step in range(1, 4):
            r, c = row - step * dr, col - step * dc
            if 0 <= r < 6 and 0 <= c < 7 and board[r][c] == player:
                count += 1
            else:
                break
        
        if count >= 4:
            board[row][col] = 0  # Revert the change
            return True
    
    board[row][col] = 0  # Revert the change
    return False

def policy(board: list[list[int]]) -> int:
    for col in range(7):
        if board[0][col] == 0:  # If the column is not full
            if is_winning_move(board, col, 1):
                return col  # Play to win

    for col in range(7):
        if board[0][col] == 0:  # If the column is not full
            if is_winning_move(board, col, -1):
                return col  # Block opponent's winning move

    # If no winning or blocking move, pick the first available column
    for col in range(7):
        if board[0][col] == 0:
            return col

    return -1  # This case theoretically should not happen
