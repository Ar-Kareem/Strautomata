
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    # List of all possible moves (row, col)
    moves = [(i, j) for i in range(3) for j in range(3) if board[i][j] != 1]

    # Check for immediate winning move
    for move in moves:
        row, col = move
        # Create a temporary board with the move applied
        temp_board = [row[:] for row in board]
        temp_board[row][col] = 1

        # Check if this move wins
        if (temp_board[row][0] == temp_board[row][1] == temp_board[row][2] == 1 or
            temp_board[0][col] == temp_board[1][col] == temp_board[2][col] == 1 or
            (row == col and temp_board[0][0] == temp_board[1][1] == temp_board[2][2] == 1) or
            (row + col == 2 and temp_board[0][2] == temp_board[1][1] == temp_board[2][0] == 1)):
            return move

    # Check for opponent's potential winning move (blocking)
    # We assume opponent's marks are where board shows 0 (not confirmed as ours)
    # This is a simplification since we don't have perfect information
    opponent_moves = [(i, j) for i in range(3) for j in range(3) if board[i][j] == 0]

    for move in opponent_moves:
        row, col = move
        # Create a temporary board with opponent's move applied
        temp_board = [row[:] for row in board]
        temp_board[row][col] = -1  # Mark as opponent's

        # Check if opponent would win with this move
        if (temp_board[row][0] == temp_board[row][1] == temp_board[row][2] == -1 or
            temp_board[0][col] == temp_board[1][col] == temp_board[2][col] == -1 or
            (row == col and temp_board[0][0] == temp_board[1][1] == temp_board[2][2] == -1) or
            (row + col == 2 and temp_board[0][2] == temp_board[1][1] == temp_board[2][0] == -1)):
            # Return the blocking move if it's available for us
            if (row, col) in moves:
                return (row, col)

    # If no immediate win or block, prioritize center
    if (1, 1) in moves:
        return (1, 1)

    # Then prioritize corners
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    available_corners = [corner for corner in corners if corner in moves]
    if available_corners:
        return random.choice(available_corners)

    # Then edges
    edges = [(0, 1), (1, 0), (1, 2), (2, 1)]
    available_edges = [edge for edge in edges if edge in moves]
    if available_edges:
        return random.choice(available_edges)

    # Fallback: return any available move (shouldn't reach here if moves exist)
    return random.choice(moves) if moves else (0, 0)
