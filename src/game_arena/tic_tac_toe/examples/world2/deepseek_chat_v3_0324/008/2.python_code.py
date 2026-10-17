
import random
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    # Check for immediate winning move
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                board[i][j] = 1
                if check_win(board, 1):
                    board[i][j] = 0  # Undo the move
                    return (i, j)
                board[i][j] = 0  # Undo the move

    # Check for opponent winning move and block
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                board[i][j] = -1
                if check_win(board, -1):
                    board[i][j] = 0  # Undo the move
                    return (i, j)
                board[i][j] = 0  # Undo the move

    # Prefer center squares
    center_squares = [(1, 1), (1, 2), (2, 1), (2, 2)]
    for i, j in center_squares:
        if board[i][j] == 0:
            return (i, j)

    # Prefer corner squares
    corners = [(0, 0), (0, 3), (3, 0), (3, 3)]
    random.shuffle(corners)  # Shuffle to avoid predictability
    for i, j in corners:
        if board[i][j] == 0:
            return (i, j)

    # Choose any available move
    available_moves = []
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                available_moves.append((i, j))
    return random.choice(available_moves)

def check_win(board: List[List[int]], player: int) -> bool:
    # Check rows
    for row in range(4):
        for col in range(2):  # Only need to check starting positions that can have 4 in a row
            if (board[row][col] == player and
                board[row][col+1] == player and
                board[row][col+2] == player and
                board[row][col+3] == player):
                return True

    # Check columns
    for col in range(4):
        for row in range(2):  # Only need to check starting positions that can have 4 in a row
            if (board[row][col] == player and
                board[row+1][col] == player and
                board[row+2][col] == player and
                board[row+3][col] == player):
                return True

    # Check diagonals (top-left to bottom-right)
    for row in range(2):
        for col in range(2):
            if (board[row][col] == player and
                board[row+1][col+1] == player and
                board[row+2][col+2] == player and
                board[row+3][col+3] == player):
                return True

    # Check diagonals (top-right to bottom-left)
    for row in range(2):
        for col in range(3, 1, -1):
            if (board[row][col] == player and
                board[row+1][col-1] == player and
                board[row+2][col-2] == player and
                board[row+3][col-3] == player):
                return True

    return False
