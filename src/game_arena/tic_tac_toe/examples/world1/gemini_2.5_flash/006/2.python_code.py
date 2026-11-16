
import math

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Determines the best move for the AI player (1) in a 3x3 Tic-Tac-Toe game using the Minimax algorithm.

    Args:
        board: A 3x3 list of lists representing the current game board.
               0: empty, 1: AI player, -1: opponent player.

    Returns:
        A tuple (row, col) indicating the optimal move.
    """
    AI_PLAYER = 1
    OPPONENT_PLAYER = -1

    def _check_win(current_board, player):
        """
        Checks if the given player has won the game on the current board.
        """
        # Check rows
        for row in current_board:
            if all(cell == player for cell in row):
                return True
        # Check columns
        for col in range(3):
            if all(current_board[row][col] == player for row in range(3)):
                return True
        # Check diagonals
        if all(current_board[i][i] == player for i in range(3)):
            return True
        if all(current_board[i][2 - i] == player for i in range(3)):
            return True
        return False

    def _get_empty_cells(current_board):
        """
        Returns a list of (row, col) tuples for all empty cells on the board.
        """
        return [(r, c) for r in range(3) for c in range(3) if current_board[r][c] == 0]

    def _minimax(current_board, is_maximizing_player):
        """
        Implements the Minimax algorithm to evaluate board states.
        """
        # Base cases: Check for terminal states (win, lose, draw)
        if _check_win(current_board, AI_PLAYER):
            return 1  # AI wins, return high score
        if _check_win(current_board, OPPONENT_PLAYER):
            return -1 # Opponent wins, return low score
        if not _get_empty_cells(current_board):
            return 0  # Draw, no empty cells and no winner

        if is_maximizing_player:
            # AI's turn: maximize the score
            best_score = -math.inf
            for r, c in _get_empty_cells(current_board):
                current_board[r][c] = AI_PLAYER  # Make the move
                score = _minimax(current_board, False) # Recurse for opponent's turn
                current_board[r][c] = 0  # Undo the move (backtrack)
                best_score = max(best_score, score)
            return best_score
        else:
            # Opponent's turn: minimize the score
            best_score = math.inf
            for r, c in _get_empty_cells(current_board):
                current_board[r][c] = OPPONENT_PLAYER # Make the opponent's move
                score = _minimax(current_board, True)  # Recurse for AI's turn
                current_board[r][c] = 0  # Undo the move (backtrack)
                best_score = min(best_score, score)
            return best_score

    # --- Main policy logic ---
    
    best_score = -math.inf
    best_move = (-1, -1)  # Initialize with an invalid move

    empty_cells = _get_empty_cells(board)

    # Optimization: If the board is completely empty, pick the center.
    # This is a common and quick optimal first move.
    if len(empty_cells) == 9:
        return (1, 1)

    # Iterate through all possible moves (empty_cells)
    for r, c in empty_cells:
        board[r][c] = AI_PLAYER  # Make a hypothetical move for the AI
        
        # After AI makes a move, it becomes the opponent's turn.
        # So we call minimax as the minimizing player.
        current_move_score = _minimax(board, False)
        
        board[r][c] = 0  # Undo the hypothetical move to restore board state

        # If this move leads to a better outcome, update best_score and best_move
        if current_move_score > best_score:
            best_score = current_move_score
            best_move = (r, c)
        
        # If we found a winning move, we can take it immediately (optional optimization)
        if best_score == 1:
            return best_move
            
    # Return the move that leads to the highest minimax score (best outcome for AI)
    return best_move

