
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

    player = 1  # AI is player 1
    opponent = -1

    # 1. Check for an immediate win
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                board[r][c] = player
                if check_win(board, player):
                    return r, c
                board[r][c] = 0  # Undo the move

    # 2. Block opponent's immediate win
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                board[r][c] = opponent
                if check_win(board, opponent):
                    return r, c
                board[r][c] = 0

    # 3. Take center positions if available (prioritize 2x2 center)
    center_cells = [(1, 1), (1, 2), (2, 1), (2, 2)]
    random.shuffle(center_cells)  # Randomize if multiple centers are open
    for r, c in center_cells:
        if board[r][c] == 0:
            return r, c
    
    # 4. Take corners if available
    corner_cells = [(0, 0), (0, 3), (3, 0), (3, 3)]
    random.shuffle(corner_cells)
    for r, c in corner_cells:
        if board[r][c] == 0:
            return r, c

    # 5. Take any available empty cell (randomly)
    empty_cells = []
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                empty_cells.append((r, c))

    if empty_cells:
        return random.choice(empty_cells)
    else:
        # Should not happen in a valid game unless it's a draw
        return -1, -1


def check_win(board: list[list[int]], player: int) -> bool:
    """
    Checks if the given player has won the game.
    """
    # Check rows
    for r in range(4):
        for c_start in range(2):  # Check 3-in-a-row in rows
            if all(board[r][c] == player for c in range(c_start, c_start + 3)):
                return True

    # Check columns
    for c in range(4):
        for r_start in range(2):  # Check 3-in-a-row in columns
            if all(board[r][c] == player for r in range(r_start, r_start + 3)):
                return True

    # Check diagonals (top-left to bottom-right)
    for r_start in range(2):
        for c_start in range(2):
            if all(board[r_start + i][c_start + i] == player for i in range(3)):
                return True

    # Check diagonals (top-right to bottom-left)
    for r_start in range(2):
        for c_start in range(2, 4):  # Start from column 2 or 3
            if all(board[r_start + i][c_start - i] == player for i in range(3)):
                return True

    return False

