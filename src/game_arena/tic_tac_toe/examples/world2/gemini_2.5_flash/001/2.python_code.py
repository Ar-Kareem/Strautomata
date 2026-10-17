
import math

# Constants for player representation
ME = 1
OPPONENT = -1
EMPTY = 0
BOARD_SIZE = 4

def check_win(board, player):
    """
    Checks if a given player has won the game.
    A win is defined as 4 pieces in a row, column, or main diagonal.
    """
    # Check rows
    for r in range(BOARD_SIZE):
        if all(board[r][c] == player for c in range(BOARD_SIZE)):
            return True
    # Check columns
    for c in range(BOARD_SIZE):
        if all(board[r][c] == player for r in range(BOARD_SIZE)):
            return True
    # Check main diagonal
    if all(board[i][i] == player for i in range(BOARD_SIZE)):
        return True
    # Check anti-diagonal
    if all(board[i][BOARD_SIZE - 1 - i] == player for i in range(BOARD_SIZE)):
        return True
    return False

def is_board_full(board):
    """
    Checks if the board is completely full (no more empty cells).
    """
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == EMPTY:
                return False
    return True

def get_empty_cells(board):
    """
    Returns a list of (row, col) tuples for all empty cells on the board.
    """
    empty_cells = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == EMPTY:
                empty_cells.append((r, c))
    return empty_cells

def evaluate(board):
    """
    Evaluates the current state of the board.
    Returns 1 if ME wins, -1 if OPPONENT wins, and 0 for a draw or ongoing game.
    """
    if check_win(board, ME):
        return 1
    if check_win(board, OPPONENT):
        return -1
    return 0 # Draw or game ongoing

def minimax(board, depth, is_maximizing_player, alpha, beta):
    """
    Implements the Minimax algorithm with Alpha-Beta Pruning.
    depth: Current depth in the search tree (not strictly used for pruning limit, but incremented).
    is_maximizing_player: True if it's the AI's (ME) turn, False if it's the OPPONENT's turn.
    alpha: The best score that the maximizing player can guarantee so far.
    beta: The best score that the minimizing player can guarantee so far.
    """
    score = evaluate(board)

    # Base cases for recursion: game over conditions
    if score == 1:  # ME wins
        return 1
    if score == -1: # OPPONENT wins
        return -1
    if is_board_full(board): # Draw
        return 0

    # If the game is not over and the board is not full, continue searching.
    if is_maximizing_player:
        max_eval = -math.inf
        for r, c in get_empty_cells(board):
            board[r][c] = ME  # Make the move
            eval = minimax(board, depth + 1, False, alpha, beta)
            board[r][c] = EMPTY # Undo the move (backtrack)
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break # Beta cutoff
        return max_eval
    else: # Minimizing player (OPPONENT)
        min_eval = math.inf
        for r, c in get_empty_cells(board):
            board[r][c] = OPPONENT # Make the move
            eval = minimax(board, depth + 1, True, alpha, beta)
            board[r][c] = EMPTY # Undo the move (backtrack)
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break # Alpha cutoff
        return min_eval

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Determines the best next move for the AI player (ME).
    Searches all possible moves using minimax with alpha-beta pruning.
    """
    best_move = (-1, -1)
    max_eval = -math.inf

    empty_cells = get_empty_cells(board)

    # Special case for the very first move to potentially speed up slightly,
    # though minimax would find a good central move anyway.
    if len(empty_cells) == BOARD_SIZE * BOARD_SIZE:
        return (1, 1) # A good central position for a 4x4 board.

    # Iterate through all available empty cells to find the best move
    for r, c in empty_cells:
        board[r][c] = ME  # Try making the move
        # Call minimax for the opponent (minimizing player)
        # after our move, assuming it's depth 0 from our perspective for this move series
        # and the opponent will play next.
        eval = minimax(board, 0, False, -math.inf, math.inf)
        board[r][c] = EMPTY # Undo the move

        if eval > max_eval:
            max_eval = eval
            best_move = (r, c)
        
        # If we found a winning move, no need to search further.
        # This is an optimization for early wins.
        if max_eval == 1:
            break

    return best_move

