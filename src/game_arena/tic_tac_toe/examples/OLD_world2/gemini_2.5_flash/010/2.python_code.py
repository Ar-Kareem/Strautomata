
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Implements a simple Tic-Tac-Toe AI policy for a 4x4 board.
    The AI attempts to win, block the opponent, and then makes random moves.
    """
    N = 4
    ME = 1
    OPPONENT = -1
    EMPTY = 0

    # 1. Check for a winning move
    for r in range(N):
        for c in range(N):
            if board[r][c] == EMPTY:
                board[r][c] = ME
                if check_win(board, ME):
                    return (r, c)
                board[r][c] = EMPTY  # backtrack

    # 2. Check for a blocking move
    for r in range(N):
        for c in range(N):
            if board[r][c] == EMPTY:
                board[r][c] = OPPONENT
                if check_win(board, OPPONENT):
                    return (r, c)
                board[r][c] = EMPTY  # backtrack

    # 3. Try to take the center (or near center) if available
    center_coords = [(1, 1), (1, 2), (2, 1), (2, 2)]
    for r, c in center_coords:
        if board[r][c] == EMPTY:
            return (r, c)

    # 4. Take any available corner
    corner_coords = [(0, 0), (0, 3), (3, 0), (3, 3)]
    for r, c in corner_coords:
        if board[r][c] == EMPTY:
            return (r, c)

    # 5. Make a random move (should only happen if all above fail)
    empty_cells = []
    for r in range(N):
        for c in range(N):
            if board[r][c] == EMPTY:
                empty_cells.append((r, c))

    if empty_cells:
        return random.choice(empty_cells)
    
    # Should not happen in a valid game, but as a fallback
    return (-1, -1)


def check_win(board: list[list[int]], player: int) -> bool:
    """
    Checks if the given player has won the 4x4 Tic-Tac-Toe game.
    A win is defined as 4 in a row, column, or diagonal.
    """
    N = 4

    # Check rows
    for r in range(N):
        for c in range(N - 3):
            if all(board[r][c+i] == player for i in range(4)):
                return True

    # Check columns
    for c in range(N):
        for r in range(N - 3):
            if all(board[r+i][c] == player for i in range(4)):
                return True

    # Check main diagonals (top-left to bottom-right)
    for r_start in range(N - 3):
        for c_start in range(N - 3):
            if all(board[r_start+i][c_start+i] == player for i in range(4)):
                return True

    # Check anti-diagonals (top-right to bottom-left)
    for r_start in range(N - 3):
        for c_start in range(3, N):
            if all(board[r_start+i][c_start-i] == player for i in range(4)):
                return True

    return False
