
import numpy as np

# Define the eight directions for queen-like movement
directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]

def get_reachable_squares(pos, board):
    """
    Given a position (row, col) and a board state, return all squares that are reachable
    by queen-like movement (orthogonal or diagonal) from the position, without crossing
    any non-empty squares (value != 0). The path must be clear, and the reachable squares
    must be empty (value == 0).
    """
    squares = []
    for dr, dc in directions:
        for step in range(1, 6):  # Max step is 5 for a 6x6 board
            r = pos[0] + dr * step
            c = pos[1] + dc * step
            # Check if the new position is within the board bounds
            if r < 0 or r >= 6 or c < 0 or c >= 6:
                break
            # If the square is empty, it is reachable
            if board[r, c] == 0:
                squares.append((r, c))
            else:
                # If non-empty, the path is blocked
                break
    return squares

def generate_all_moves(board, player):
    """
    Generate all possible moves for the given player (1 for us, 2 for opponent).
    Each move is a tuple: (from_pos, to_pos, arrow_pos)
    """
    moves = []
    # Find all amazon positions for the player
    amazon_positions = []
    for r in range(6):
        for c in range(6):
            if board[r, c] == player:
                amazon_positions.append((r, c))

    for from_pos in amazon_positions:
        to_positions = get_reachable_squares(from_pos, board)
        for to_pos in to_positions:
            # Create a copy of the board to simulate the move
            board_copy = board.copy()
            # Move the amazon: set from_pos to empty and to_pos to player's amazon
            board_copy[from_pos] = 0
            board_copy[to_pos] = player
            # Generate all possible arrow shots from the new position
            arrow_positions = get_reachable_squares(to_pos, board_copy)
            for arrow_pos in arrow_positions:
                move = (from_pos, to_pos, arrow_pos)
                moves.append(move)
    return moves

def policy(board):
    """
    Given the current board state (6x6 numpy array), return a legal move string in the format
    "from_row,from_col:to_row,to_col:arrow_row,arrow_col".
    The policy selects the move that maximizes the difference between the number of moves
    available to the player and the opponent after the move.
    """
    # Generate all possible moves for the player (us)
    our_moves = generate_all_moves(board, player=1)
    
    # If there are no legal moves, we cannot proceed (though the environment should not call this in such cases)
    if not our_moves:
        # As a fallback, return a random move or raise an error, but per rules, this should not happen
        raise ValueError("No legal moves available.")

    best_score = -float('inf')
    best_move = None

    for move in our_moves:
        from_pos, to_pos, arrow_pos = move
        # Simulate the move on a copy of the board
        new_board = board.copy()
        new_board[from_pos] = 0  # Vacate the from square
        new_board[to_pos] = 1   # Place the amazon at to_pos
        new_board[arrow_pos] = -1  # Place the arrow

        # Generate all moves for the opponent on the new board
        opponent_moves = generate_all_moves(new_board, player=2)
        opponent_move_count = len(opponent_moves)

        # Generate all moves for us on the new board
        our_moves_new = generate_all_moves(new_board, player=1)
        our_move_count = len(our_moves_new)

        # Calculate the score: difference between our moves and opponent's moves
        score = our_move_count - opponent_move_count

        # Update the best move if this score is higher
        if score > best_score:
            best_score = score
            best_move = move

    # Format the best move as a string
    from_r, from_c = best_move[0]
    to_r, to_c = best_move[1]
    arrow_r, arrow_c = best_move[2]
    move_string = f"{from_r},{from_c}:{to_r},{to_c}:{arrow_r},{arrow_c}"
    return move_string
