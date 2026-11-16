
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    # List of all possible moves (row, col)
    moves = [(i, j) for i in range(3) for j in range(3) if board[i][j] != 1]

    # Check for immediate winning move
    for move in moves:
        row, col = move
        # Create a temporary board with this move
        temp_board = [row[:] for row in board]
        temp_board[row][col] = 1

        # Check if this move wins
        if (temp_board[row][0] == temp_board[row][1] == temp_board[row][2] == 1 or
            temp_board[0][col] == temp_board[1][col] == temp_board[2][col] == 1 or
            (row == col and temp_board[0][0] == temp_board[1][1] == temp_board[2][2] == 1) or
            (row + col == 2 and temp_board[0][2] == temp_board[1][1] == temp_board[2][0] == 1)):
            return move

    # Check for opponent's potential winning moves (blocking)
    # We assume opponent has marked cells where we don't have confirmed marks (0s)
    # This is a heuristic since we don't have perfect information
    for move in moves:
        row, col = move
        # Create a temporary board assuming opponent has this cell
        temp_board = [row[:] for row in board]
        temp_board[row][col] = -1  # -1 represents opponent's mark

        # Check if opponent would win with this move
        if (temp_board[row][0] == temp_board[row][1] == temp_board[row][2] == -1 or
            temp_board[0][col] == temp_board[1][col] == temp_board[2][col] == -1 or
            (row == col and temp_board[0][0] == temp_board[1][1] == temp_board[2][2] == -1) or
            (row + col == 2 and temp_board[0][2] == temp_board[1][1] == temp_board[2][0] == -1)):
            return move

    # Prefer center if available
    if (1, 1) in moves:
        return (1, 1)

    # Prefer corners over edges
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    available_corners = [c for c in corners if c in moves]
    if available_corners:
        return random.choice(available_corners)

    # If no strategic move, choose randomly from available moves
    return random.choice(moves)
