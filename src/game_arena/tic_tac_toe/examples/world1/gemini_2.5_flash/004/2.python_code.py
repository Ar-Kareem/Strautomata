
import math

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Determines the optimal next move for a Tic Tac Toe game using the Minimax algorithm.

    Args:
        board: A 3x3 list of lists representing the Tic Tac Toe board.
               0: empty, 1: AI's piece, -1: Opponent's piece.

    Returns:
        A tuple (row, col) indicating the optimal move.
    """

    PLAYER = 1  # Represents our AI player
    OPPONENT = -1 # Represents the opponent player
    EMPTY = 0 # Represents an empty cell

    def check_win(current_board: list[list[int]], player: int) -> bool:
        """
        Checks if the given player has won the game on the current board.
        """
        # Check rows
        for r in range(3):
            if all(current_board[r][c] == player for c in range(3)):
                return True
        # Check columns
        for c in range(3):
            if all(current_board[r][c] == player for r in range(3)):
                return True
        # Check diagonals
        if all(current_board[i][i] == player for i in range(3)):
            return True
        if all(current_board[i][2 - i] == player for i in range(3)):
            return True
        return False

    def get_empty_cells(current_board: list[list[int]]) -> list[tuple[int, int]]:
        """
        Returns a list of (row, col) tuples for all empty cells on the board.
        """
        empty_cells = []
        for r in range(3):
            for c in range(3):
                if current_board[r][c] == EMPTY:
                    empty_cells.append((r, c))
        return empty_cells

    def minimax(current_board: list[list[int]], is_maximizing_player: bool) -> int:
        """
        The Minimax algorithm function.
        Recursively evaluates board states and returns the best possible score.

        Args:
            current_board: The current state of the Tic Tac Toe board.
            is_maximizing_player: True if it's the AI's turn (maximizing player),
                                  False if it's the opponent's turn (minimizing player).

        Returns:
            The score of the current board state from the maximizing player's perspective.
            1: AI wins, -1: Opponent wins, 0: Draw.
        """
        # Base cases: Check for terminal states (win/loss/draw)
        if check_win(current_board, PLAYER):
            return 1  # AI wins
        if check_win(current_board, OPPONENT):
            return -1 # Opponent wins
        if not get_empty_cells(current_board):
            return 0  # Draw

        if is_maximizing_player:
            # AI's turn: try to maximize the score
            best_score = -math.inf
            for r, c in get_empty_cells(current_board):
                current_board[r][c] = PLAYER  # Make the move
                score = minimax(current_board, False) # Recurse for opponent's turn
                current_board[r][c] = EMPTY   # Undo the move
                best_score = max(best_score, score)
            return best_score
        else:
            # Opponent's turn: try to minimize the score
            best_score = math.inf
            for r, c in get_empty_cells(current_board):
                current_board[r][c] = OPPONENT # Make the move
                score = minimax(current_board, True) # Recurse for AI's turn
                current_board[r][c] = EMPTY    # Undo the move
                best_score = min(best_score, score)
            return best_score

    best_move = None
    best_score = -math.inf
    
    # Get all cells where the AI can make a move
    available_moves = get_empty_cells(board)

    # Iterate through all available moves to find the one that leads to the best outcome
    for r, c in available_moves:
        board[r][c] = PLAYER  # Simulate making this move for the AI
        
        # Evaluate the resulting board state from the *opponent's* perspective (minimizing player)
        # as it will be their turn next.
        current_score = minimax(board, False) 
        
        board[r][c] = EMPTY   # Undo the move to restore the board for the next simulation

        if current_score > best_score:
            best_score = current_score
            best_move = (r, c)
            
    # In case the board is full (which shouldn't happen if policy is called for a valid turn)
    # or if for some reason best_move wasn't set, return the first available move.
    # With a correctly implemented minimax and a non-full board for our turn, best_move will always be set.
    if best_move is None and available_moves:
        return available_moves[0]

    return best_move
