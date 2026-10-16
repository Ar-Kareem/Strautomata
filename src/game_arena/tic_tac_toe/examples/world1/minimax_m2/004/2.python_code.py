
import sys

# Global cache for memoization
cache = {}

# Winning lines for Tic Tac Toe
winning_lines = [
    [(0, 0), (0, 1), (0, 2)],  # first row
    [(1, 0), (1, 1), (1, 2)],  # second row
    [(2, 0), (2, 1), (2, 2)],  # third row
    [(0, 0), (1, 0), (2, 0)],  # first column
    [(0, 1), (1, 1), (2, 1)],  # second column
    [(0, 2), (1, 2), (2, 2)],  # third column
    [(0, 0), (1, 1), (2, 2)],  # main diagonal
    [(0, 2), (1, 1), (2, 0)]   # anti-diagonal
]

def board_to_tuple(board):
    """Convert the board to a tuple of tuples for hashing."""
    return tuple(tuple(row) for row in board)

def check_winner(board):
    """Check if there is a winner on the board."""
    for line in winning_lines:
        values = [board[i][j] for i, j in line]
        if values[0] != 0 and values[0] == values[1] == values[2]:
            return values[0]  # Return the winner
    return None  # No winner

def is_draw(board):
    """Check if the board is a draw."""
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                return False
    return True

def minimax(board):
    """
    Minimax function with memoization.
    Returns the best score and best move for the current player.
    """
    board_key = board_to_tuple(board)
    if board_key in cache:
        return cache[board_key]

    # Check if the game is over
    winner = check_winner(board)
    if winner is not None:
        # Game over, someone won
        if winner == 1:
            value = 10  # I win
        else:
            value = -10  # Opponent wins
        best_move = None
        cache[board_key] = (value, best_move)
        return value, best_move

    if is_draw(board):
        value = 0  # Draw
        best_move = None
        cache[board_key] = (value, best_move)
        return value, best_move

    # Determine whose turn it is
    count_1 = sum(1 for i in range(3) for j in range(3) if board[i][j] == 1)
    count_minus1 = sum(1 for i in range(3) for j in range(3) if board[i][j] == -1)
    if count_1 == count_minus1:
        is_my_turn = True
    elif count_1 == count_minus1 + 1:
        is_my_turn = False
    else:
        # Invalid state, but should not happen in a valid game
        raise ValueError("Invalid board state")

    # Generate all possible moves
    empty_cells = [(i, j) for i in range(3) for j in range(3) if board[i][j] == 0]

    if is_my_turn:
        # My turn: maximize the value
        best_value = -float('inf')
        best_move = None
        for move in empty_cells:
            # Simulate the move: place 1
            new_board = [row[:] for row in board]  # Deep copy
            new_board[move[0]][move[1]] = 1
            value, _ = minimax(new_board)
            # Adjust the value by subtracting 1 for the move made
            adjusted_value = value - 1
            if adjusted_value > best_value:
                best_value = adjusted_value
                best_move = move
        cache[board_key] = (best_value, best_move)
        return best_value, best_move
    else:
        # Opponent's turn: minimize the value
        best_value = float('inf')
        best_move = None
        for move in empty_cells:
            # Simulate the move: place -1
            new_board = [row[:] for row in board]  # Deep copy
            new_board[move[0]][move[1]] = -1
            value, _ = minimax(new_board)
            # Adjust the value by subtracting 1 for the move made
            adjusted_value = value - 1
            if adjusted_value < best_value:
                best_value = adjusted_value
                best_move = move
        cache[board_key] = (best_value, best_move)
        return best_value, best_move

def policy(board):
    """
    Policy function that returns the best move for the current player.
    """
    # Clear the cache if it's the first call or if needed, but we'll keep it for efficiency
    # Call minimax to get the best move
    value, best_move = minimax(board)
    return best_move
