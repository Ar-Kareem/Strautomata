
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Determines the next move for a Tic Tac Toe game.

    Args:
        board: A 3x3 list of lists representing the Tic Tac Toe board.
               0: empty, 1: player (AI), -1: opponent.

    Returns:
        A tuple (row, col) indicating the chosen move.
    """

    player = 1  # AI is player 1

    # 1. Check for a winning move
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                board[r][c] = player
                if check_win(board, player):
                    return r, c
                board[r][c] = 0  # Undo the move

    # 2. Check to block opponent's winning move
    opponent = -1
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                board[r][c] = opponent
                if check_win(board, opponent):
                    return r, c
                board[r][c] = 0  # Undo the move

    # 3. Try to take the center if available
    if board[1][1] == 0:
        return 1, 1

    # 4. Try to take a corner if available
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    random.shuffle(corners)  # Randomize corner choice
    for r, c in corners:
        if board[r][c] == 0:
            return r, c

    # 5. Take any available side
    sides = [(0, 1), (1, 0), (1, 2), (2, 1)]
    random.shuffle(sides)  # Randomize side choice
    for r, c in sides:
        if board[r][c] == 0:
            return r, c
    
    # Should not be reached in a valid game unless board is full
    # In case of full board, return a random empty spot (shouldn't happen)
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                return r, c

    return -1, -1 # Should ideally not reach here

def check_win(board: list[list[int]], player: int) -> bool:
    """
    Checks if the given player has won the game.
    """
    # Check rows
    for r in range(3):
        if all(board[r][c] == player for c in range(3)):
            return True
    # Check columns
    for c in range(3):
        if all(board[r][c] == player for r in range(3)):
            return True
    # Check diagonals
    if all(board[i][i] == player for i in range(3)):
        return True
    if all(board[i][2 - i] == player for i in range(3)):
        return True
    return False
