
import math

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Determines the next move for the Tic Tac Toe AI using the Minimax algorithm.
    1: AI, -1: Opponent, 0: Empty
    """
    
    # All possible winning lines (rows, columns, diagonals)
    WIN_LINES = [
        [(0, 0), (0, 1), (0, 2)],
        [(1, 0), (1, 1), (1, 2)],
        [(2, 0), (2, 1), (2, 2)],
        [(0, 0), (1, 0), (2, 0)],
        [(0, 1), (1, 1), (2, 1)],
        [(0, 2), (1, 2), (2, 2)],
        [(0, 0), (1, 1), (2, 2)],
        [(0, 2), (1, 1), (2, 0)]
    ]

    def check_winner(b, player):
        """Checks if the given player has won on the board."""
        for line in WIN_LINES:
            if all(b[r][c] == player for r, c in line):
                return True
        return False

    def get_empty_cells(b):
        """Returns a list of (row, col) tuples for empty cells."""
        return [(r, c) for r in range(3) for c in range(3) if b[r][c] == 0]

    def minimax(b, depth, is_maximizing):
        """
        Recursive Minimax algorithm.
        Returns the score of the board state.
        """
        # Terminal states
        if check_winner(b, 1):
            return 10 - depth
        if check_winner(b, -1):
            return depth - 10
        
        empty = get_empty_cells(b)
        if not empty:
            return 0  # Draw

        if is_maximizing:
            best_val = -math.inf
            for r, c in empty:
                b[r][c] = 1
                val = minimax(b, depth + 1, False)
                b[r][c] = 0  # Backtrack
                best_val = max(best_val, val)
            return best_val
        else:
            best_val = math.inf
            for r, c in empty:
                b[r][c] = -1
                val = minimax(b, depth + 1, True)
                b[r][c] = 0  # Backtrack
                best_val = min(best_val, val)
            return best_val

    # --- Move Selection ---

    empty_cells = get_empty_cells(board)
    
    # Optimal opening: If the board is empty, take the center
    if len(empty_cells) == 9:
        return (1, 1)

    best_score = -math.inf
    best_move = empty_cells[0]  # Default to first available move

    # Find the move with the highest minimax score
    for r, c in empty_cells:
        board[r][c] = 1
        move_score = minimax(board, 0, False)
        board[r][c] = 0  # Backtrack

        if move_score > best_score:
            best_score = move_score
            best_move = (r, c)

    return best_move
