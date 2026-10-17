
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Determines the next move for a 4x4 Tic Tac Toe game.

    Args:
        board: A 4x4 list of lists representing the game board.
               0: empty, 1: AI (you), -1: opponent.

    Returns:
        A tuple of two integers (row, col) indicating the chosen move.
    """

    player = 1
    opponent = -1

    # 1. Check for winning move
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                board[r][c] = player
                if check_win(board, player):
                    return r, c
                board[r][c] = 0  # Undo move

    # 2. Check for blocking opponent's winning move
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                board[r][c] = opponent
                if check_win(board, opponent):
                    return r, c
                board[r][c] = 0  # Undo move

    # 3. Prioritize center squares (for 4x4, these could be (1,1), (1,2), (2,1), (2,2))
    center_squares = [(1, 1), (1, 2), (2, 1), (2, 2)]
    random.shuffle(center_squares)  # Randomize order to avoid predictable play
    for r, c in center_squares:
        if board[r][c] == 0:
            return r, c

    # 4. Prioritize corner squares
    corner_squares = [(0, 0), (0, 3), (3, 0), (3, 3)]
    random.shuffle(corner_squares)
    for r, c in corner_squares:
        if board[r][c] == 0:
            return r, c

    # 5. Take any available empty square (randomly)
    empty_cells = []
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                empty_cells.append((r, c))

    if empty_cells:
        return random.choice(empty_cells)

    # Should not happen in a valid game
    return -1, -1


def check_win(board: list[list[int]], player: int) -> bool:
    """
    Checks if the given player has won the game.
    """
    # Check rows
    for r in range(4):
        for c in range(2):  # Check 3 in a row
            if all(board[r][c+i] == player for i in range(3)):
                return True
        for c in range(1, 3): # Check remaining possible 3 in a row groups
            if all(board[r][c+i] == player for i in range(3)):
                return True

    # Check columns
    for c in range(4):
        for r in range(2):  # Check 3 in a column
            if all(board[r+i][c] == player for i in range(3)):
                return True
        for r in range(1, 3): # Check remaining possible 3 in a column groups
            if all(board[r+i][c] == player for i in range(3)):
                return True

    # Check main diagonals (top-left to bottom-right)
    for r_start in range(2):
        for c_start in range(2):
            if all(board[r_start+i][c_start+i] == player for i in range(3)):
                return True

    # Check anti-diagonals (top-right to bottom-left)
    for r_start in range(2):
        for c_start in range(2, 4):
            if all(board[r_start+i][c_start-i] == player for i in range(3)):
                return True

    return False

