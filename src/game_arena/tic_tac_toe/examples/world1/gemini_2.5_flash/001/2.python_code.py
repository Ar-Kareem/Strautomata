
import math

def check_winner(board: list[list[int]]) -> int:
    """
    Checks if there's a winner on the board.
    Returns 1 if player 1 wins, -1 if player -1 wins, 0 otherwise.
    """
    # Check rows
    for row in board:
        if all(cell == 1 for cell in row):
            return 1
        if all(cell == -1 for cell in row):
            return -1

    # Check columns
    for col_idx in range(3):
        if all(board[row_idx][col_idx] == 1 for row_idx in range(3)):
            return 1
        if all(board[row_idx][col_idx] == -1 for row_idx in range(3)):
            return -1

    # Check diagonals
    if (board[0][0] == board[1][1] == board[2][2] == 1) or \
       (board[0][2] == board[1][1] == board[2][0] == 1):
        return 1
    if (board[0][0] == board[1][1] == board[2][2] == -1) or \
       (board[0][2] == board[1][1] == board[2][0] == -1):
        return -1

    # No winner yet
    return 0

def get_empty_cells(board: list[list[int]]) -> list[tuple[int, int]]:
    """
    Returns a list of (row, col) tuples for all empty cells on the board.
    """
    empty_cells = []
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                empty_cells.append((r, c))
    return empty_cells

def minimax(board: list[list[int]], depth: int, is_maximizing_player: bool) -> int:
    """
    Implements the Minimax algorithm to find the best score for the current board state.
    """
    winner = check_winner(board)
    if winner == 1:
        # Player 1 (us) wins: return a positive score, prioritizing faster wins
        return 10 - depth
    if winner == -1:
        # Player -1 (opponent) wins: return a negative score, prioritizing slower losses
        return -10 + depth

    empty_cells = get_empty_cells(board)
    if not empty_cells:
        # Draw condition: no winner and no empty cells left
        return 0

    if is_maximizing_player: # Our turn (player 1)
        best_eval = -math.inf
        for r, c in empty_cells:
            board[r][c] = 1  # Make the move
            eval = minimax(board, depth + 1, False) # Recurse for opponent
            board[r][c] = 0  # Undo the move
            best_eval = max(best_eval, eval)
        return best_eval
    else: # Opponent's turn (player -1)
        best_eval = math.inf
        for r, c in empty_cells:
            board[r][c] = -1 # Make the move
            eval = minimax(board, depth + 1, True) # Recurse for us
            board[r][c] = 0  # Undo the move
            best_eval = min(best_eval, eval)
        return best_eval


def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Determines the next optimal move for a 3x3 Tic-Tac-Toe game using Minimax.

    Args:
        board: A 3x3 list of lists representing the Tic-Tac-Toe board.
               0: empty, 1: your piece, -1: opponent's piece.

    Returns:
        A tuple (row, col) indicating the chosen move.
    """
    # Special handling for the very first move (empty board)
    # The center (1,1) is generally the strongest opening move in Tic-Tac-Toe.
    if all(cell == 0 for row in board for cell in row):
        return (1, 1)

    best_score = -math.inf
    best_move = None
    
    empty_cells = get_empty_cells(board)
    
    # This state should ideally not be reached if the game logic correctly
    # calls `policy` only when a move is possible.
    if not empty_cells:
        raise ValueError("Policy called on a full board with no possible moves.")

    # Iterate through all available empty cells to find the best possible move
    for r, c in empty_cells:
        board[r][c] = 1  # Temporarily make the move for 'us' (player 1)
        
        # Calculate the score for this move by simulating the rest of the game
        # Opponent will play next (is_maximizing_player=False)
        score = minimax(board, 0, False)
        
        board[r][c] = 0  # Undo the move to restore the board state for the next potential move
        
        if score > best_score:
            best_score = score
            best_move = (r, c)
            
    return best_move
