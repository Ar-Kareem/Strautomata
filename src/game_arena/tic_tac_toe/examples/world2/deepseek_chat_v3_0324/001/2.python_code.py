
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Check for immediate winning move
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                # Check if placing here would win
                board[i][j] = 1
                if check_win(board, 1):
                    board[i][j] = 0  # undo temporary placement
                    return (i, j)
                board[i][j] = 0  # undo temporary placement

    # Check for opponent's winning move to block
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                board[i][j] = -1
                if check_win(board, -1):
                    board[i][j] = 0  # undo temporary placement
                    return (i, j)
                board[i][j] = 0  # undo temporary placement

    # Prioritize center positions
    center_positions = [(1, 1), (1, 2), (2, 1), (2, 2)]
    for i, j in center_positions:
        if board[i][j] == 0:
            return (i, j)

    # Then try corners
    corners = [(0, 0), (0, 3), (3, 0), (3, 3)]
    for i, j in corners:
        if board[i][j] == 0:
            return (i, j)

    # Finally, pick any available position
    empty_positions = []
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                empty_positions.append((i, j))
    return random.choice(empty_positions)

def check_win(board: list[list[int]], player: int) -> bool:
    # Check rows
    for row in board:
        if all(cell == player for cell in row):
            return True
    
    # Check columns
    for j in range(4):
        if all(board[i][j] == player for i in range(4)):
            return True
    
    # Check diagonals
    if all(board[i][i] == player for i in range(4)):
        return True
    if all(board[i][3-i] == player for i in range(4)):
        return True
    
    return False
