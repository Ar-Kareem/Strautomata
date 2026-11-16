
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Implements a policy for a 4x4 Tic Tac Toe game.

    Args:
        board: A 4x4 list of lists representing the game board.
               0: empty, 1: player (AI), -1: opponent.

    Returns:
        A tuple (row, col) indicating the chosen move.
    """

    n = 4  # Board size

    # Helper function to check if a player has won
    def check_win(current_board, player):
        # Check rows
        for r in range(n):
            if all(current_board[r][c] == player for c in range(n)):
                return True
        # Check columns
        for c in range(n):
            if all(current_board[r][c] == player for r in range(n)):
                return True
        # Check main diagonal
        if all(current_board[i][i] == player for i in range(n)):
            return True
        # Check anti-diagonal
        if all(current_board[i][n - 1 - i] == player for i in range(n)):
            return True
        return False

    # Check for immediate win opportunities
    for r in range(n):
        for c in range(n):
            if board[r][c] == 0:
                temp_board = [row[:] for row in board]  # Create a copy
                temp_board[r][c] = 1  # Try placing our piece
                if check_win(temp_board, 1):
                    return (r, c)

    # Check for opponent immediate win blocking opportunities
    for r in range(n):
        for c in range(n):
            if board[r][c] == 0:
                temp_board = [row[:] for row in board]
                temp_board[r][c] = -1  # Try placing opponent's piece
                if check_win(temp_board, -1):
                    return (r, c)

    # Prioritize center spots
    center_moves = [(1, 1), (1, 2), (2, 1), (2, 2)]
    for r, c in center_moves:
        if board[r][c] == 0:
            return (r, c)

    # Prioritize corner spots
    corner_moves = [(0, 0), (0, 3), (3, 0), (3, 3)]
    for r, c in corner_moves:
        if board[r][c] == 0:
            return (r, c)

    # Otherwise, choose a random empty spot
    empty_cells = []
    for r in range(n):
        for c in range(n):
            if board[r][c] == 0:
                empty_cells.append((r, c))

    if empty_cells:
        return random.choice(empty_cells)
    
    # Should not happen in a valid game unless the board is full
    return (-1, -1) 


if __name__ == '__main__':
    # Example usage:
    # An empty board
    empty_board = [
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0]
    ]
    print(f"Move on empty board: {policy(empty_board)}")

    # Board with a win opportunity for AI
    win_board = [
        [1, 1, 1, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0]
    ]
    print(f"Move to win (should be (0, 3)): {policy(win_board)}")

    # Board with a blocking opportunity for AI
    block_board = [
        [-1, -1, -1, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0]
    ]
    print(f"Move to block (should be (0, 3)): {policy(block_board)}")

    # Board with a preference for center
    center_pref_board = [
        [1, 0, 0, -1],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [-1, 0, 0, 1]
    ]
    move = policy(center_pref_board)
    print(f"Move with preference for center (e.g., (1,1), (1,2), (2,1), (2,2)): {move}")
    assert move in [(1,1), (1,2), (2,1), (2,2)], "Should pick a center spot"

    # Board with a preference for corner if center is taken
    corner_pref_board = [
        [1, 0, 0, -1],
        [0, 1, -1, 0],
        [0, -1, 1, 0],
        [-1, 0, 0, 1]
    ]
    move = policy(corner_pref_board)
    print(f"Move with preference for corner (e.g., (0,0), (0,3), (3,0), (3,3)): {move}")
    assert move in [(0,0), (0,3), (3,0), (3,3)], "Should pick a corner spot"
