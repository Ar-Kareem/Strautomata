
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Selects the next move for a Tic Tac Toe game.

    Args:
        board: A 3x3 list of lists representing the game board.
               0 represents an empty cell, 1 represents the AI's move, and -1 represents the opponent's move.

    Returns:
        A tuple of two integers (row, col) indicating the chosen move.
    """

    # 1. Check for winning move
    for row in range(3):
        if sum(board[row]) == 2:
            for col in range(3):
                if board[row][col] == 0:
                    return row, col

    for col in range(3):
        if sum(board[row][col] for row in range(3)) == 2:
            for row in range(3):
                if board[row][col] == 0:
                    return row, col

    if board[0][0] + board[1][1] + board[2][2] == 2:
        for i in range(3):
            if board[i][i] == 0:
                return i, i

    if board[0][2] + board[1][1] + board[2][0] == 2:
        if board[0][2] == 0: return 0, 2
        if board[1][1] == 0: return 1, 1
        if board[2][0] == 0: return 2, 0
    

    # 2. Check for blocking move
    for row in range(3):
        if sum(board[row]) == -2:
            for col in range(3):
                if board[row][col] == 0:
                    return row, col

    for col in range(3):
        if sum(board[row][col] for row in range(3)) == -2:
            for row in range(3):
                if board[row][col] == 0:
                    return row, col

    if board[0][0] + board[1][1] + board[2][2] == -2:
        for i in range(3):
            if board[i][i] == 0:
                return i, i

    if board[0][2] + board[1][1] + board[2][0] == -2:
        if board[0][2] == 0: return 0, 2
        if board[1][1] == 0: return 1, 1
        if board[2][0] == 0: return 2, 0
    

    # 3. Check for center move
    if board[1][1] == 0:
        return 1, 1

    # 4. Check for corner move
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    available_corners = [(row, col) for row, col in corners if board[row][col] == 0]
    if available_corners:
        return random.choice(available_corners)

    # 5. Pick a random move
    available_moves = []
    for row in range(3):
        for col in range(3):
            if board[row][col] == 0:
                available_moves.append((row, col))

    if available_moves:
        return random.choice(available_moves)

    # No moves left (should not happen in a valid game)
    return -1, -1
