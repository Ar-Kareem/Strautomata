
import math

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Determines the best move for a Tic Tac Toe game using the Minimax algorithm
    with Alpha-Beta pruning.

    Args:
        board: A 3x3 list of lists representing the Tic Tac Toe board.
               0: Empty, 1: Your piece, -1: Opponent's piece.

    Returns:
        A tuple (row, col) representing the optimal move.
    """

    def check_win(current_board, player):
        """Checks if the given player has won the game."""
        # Check rows
        for row in range(3):
            if all(current_board[row][c] == player for c in range(3)):
                return True
        # Check columns
        for col in range(3):
            if all(current_board[r][col] == player for r in range(3)):
                return True
        # Check diagonals
        if (current_board[0][0] == player and current_board[1][1] == player and current_board[2][2] == player) or \
           (current_board[0][2] == player and current_board[1][1] == player and current_board[2][0] == player):
            return True
        return False

    def is_board_full(current_board):
        """Checks if the board is completely filled."""
        for row in current_board:
            for cell in row:
                if cell == 0:
                    return False
        return True

    def get_empty_cells(current_board):
        """Returns a list of (row, col) tuples for all empty cells."""
        empty_cells = []
        for r in range(3):
            for c in range(3):
                if current_board[r][c] == 0:
                    empty_cells.append((r, c))
        return empty_cells

    def minimax(current_board, is_maximizing_player, alpha, beta):
        """
        Minimax algorithm with Alpha-Beta pruning to evaluate board states.

        Args:
            current_board: The current state of the board.
            is_maximizing_player: True if the current call is for the maximizing player (our AI),
                                  False for the minimizing player (opponent).
            alpha: The best (highest) score that the maximizing player can guarantee so far.
            beta: The best (lowest) score that the minimizing player can guarantee so far.

        Returns:
            The score of the current board state from the perspective of the maximizing player.
            1 for AI win, -1 for opponent win, 0 for draw.
        """
        # Base cases: Check for terminal states
        if check_win(current_board, 1):
            return 1  # AI wins
        if check_win(current_board, -1):
            return -1 # Opponent wins
        if is_board_full(current_board):
            return 0  # Draw

        if is_maximizing_player:
            max_eval = -math.inf
            for r, c in get_empty_cells(current_board):
                current_board[r][c] = 1  # Make AI's move
                eval = minimax(current_board, False, alpha, beta) # Opponent's turn
                current_board[r][c] = 0  # Undo move
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break  # Alpha-beta pruning
            return max_eval
        else:  # Minimizing player (opponent)
            min_eval = math.inf
            for r, c in get_empty_cells(current_board):
                current_board[r][c] = -1 # Make opponent's move
                eval = minimax(current_board, True, alpha, beta) # AI's turn
                current_board[r][c] = 0  # Undo move
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break  # Alpha-beta pruning
            return min_eval

    best_score = -math.inf
    best_move = None
    
    # Initialize alpha and beta for the top-level search (for the moves our AI can make)
    alpha = -math.inf
    beta = math.inf # Beta here will only be used internally by subsequent minimax calls.

    empty_cells = get_empty_cells(board)

    # Iterate through all possible moves, calculate their score using minimax
    # and choose the move that leads to the best possible outcome.
    for r, c in empty_cells:
        board[r][c] = 1  # Make a temporary move for calculation
        
        # After our move, it's the opponent's turn (False for is_maximizing_player)
        score = minimax(board, False, alpha, beta)
        
        board[r][c] = 0  # Undo the temporary move

        if score > best_score:
            best_score = score
            best_move = (r, c)
        
        # Update alpha for the current level (our possible moves)
        alpha = max(alpha, score) 
        # In this top-level loop, 'beta' is not directly used for pruning our own moves,
        # as we want to find the best move among all available options.
        # However, the updated 'alpha' value is passed down to minimax calls.

    # If for some reason (e.g. board is full, game is over, though policy should not be called then)
    # best_move is still None, pick the first available empty cell defensively.
    # This scenario should ideally not be reached if the game is playable.
    if best_move is None and empty_cells:
        return empty_cells[0]
    
    return best_move

