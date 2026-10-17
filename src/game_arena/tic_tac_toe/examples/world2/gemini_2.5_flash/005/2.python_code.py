
import math

# Constants for players
ME = 1
OPPONENT = -1
EMPTY = 0

BOARD_SIZE = 4

# Scoring for evaluation function
WIN_SCORE = 10000000  # Must be significantly larger than any heuristic score
# Heuristic scores for potential lines. Positive for opportunities for ME, negative for threats from OPPONENT.
THREE_IN_A_ROW_OPPORTUNITY = 1000 # E.g., _XXX_
THREE_IN_A_ROW_THREAT = -1000    # E.g., _OOO_
TWO_IN_A_ROW_OPPORTUNITY = 100  # E.g., _XX__
TWO_IN_A_ROW_THREAT = -100     # E.g., _OO__

CENTER_SCORE_WEIGHT = 20 # Advantage for controlling center cells


def get_all_lines(board):
    """
    Generates all possible 4-cell lines on the 4x4 board that can lead to a win.
    These include rows, columns, and the two main diagonals.
    """
    lines = []

    # Rows
    for r in range(BOARD_SIZE):
        lines.append([board[r][c] for c in range(BOARD_SIZE)])
    
    # Columns
    for c in range(BOARD_SIZE):
        lines.append([board[r][c] for r in range(BOARD_SIZE)])

    # Main diagonal (top-left to bottom-right)
    lines.append([board[i][i] for i in range(BOARD_SIZE)])
    
    # Anti-diagonal (top-right to bottom-left)
    lines.append([board[i][BOARD_SIZE - 1 - i] for i in range(BOARD_SIZE)])
    
    return lines

def evaluate(board):
    """
    Evaluates the current board state from the perspective of ME (maximizing player).
    Positive scores are good for ME, negative scores are good for OPPONENT.
    Returns WIN_SCORE if ME wins, -WIN_SCORE if OPPONENT wins.
    Otherwise, returns a heuristic score based on threats and opportunities.
    """
    score = 0

    lines = get_all_lines(board)

    for line in lines:
        me_count = line.count(ME)
        opponent_count = line.count(OPPONENT)
        empty_count = line.count(EMPTY)

        # Immediate wins: highest priority
        if me_count == 4:
            return WIN_SCORE
        if opponent_count == 4:
            return -WIN_SCORE

        # Opportunities and threats: heuristic scoring
        # If the line contains only ME's pieces and empty spaces
        if opponent_count == 0:
            if me_count == 3 and empty_count == 1:
                score += THREE_IN_A_ROW_OPPORTUNITY
            elif me_count == 2 and empty_count == 2:
                score += TWO_IN_A_ROW_OPPORTUNITY
        # If the line contains only OPPONENT's pieces and empty spaces
        elif me_count == 0:
            if opponent_count == 3 and empty_count == 1:
                score += THREE_IN_A_ROW_THREAT
            elif opponent_count == 2 and empty_count == 2:
                score += TWO_IN_A_ROW_THREAT
    
    # Center control: heuristic bonus for occupying central cells
    # For a 4x4 board, (1,1), (1,2), (2,1), (2,2) are considered central.
    center_cells = [(1,1), (1,2), (2,1), (2,2)]
    for r, c in center_cells:
        if board[r][c] == ME:
            score += CENTER_SCORE_WEIGHT
        elif board[r][c] == OPPONENT:
            score -= CENTER_SCORE_WEIGHT

    return score

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

def is_game_over(board):
    """
    Checks if the game has ended (win for either player or a draw).
    Returns (True, winner) or (False, None).
    Winner can be ME, OPPONENT, or EMPTY (for a draw).
    """
    # Use evaluate to quickly check for win conditions.
    # The evaluate function returns WIN_SCORE or -WIN_SCORE immediately if a win is found.
    current_eval = evaluate(board)
    if current_eval >= WIN_SCORE:
        return True, ME # ME wins
    if current_eval <= -WIN_SCORE:
        return True, OPPONENT # OPPONENT wins

    # Check for a draw (board full and no winner)
    if not get_empty_cells(board):
        return True, EMPTY # Draw

    return False, None # Game is not over

def minimax(board, depth, maximizing_player, alpha, beta):
    """
    Minimax algorithm with Alpha-Beta pruning to find the best move.
    """
    game_over, winner = is_game_over(board)
    if game_over:
        if winner == ME: return WIN_SCORE, None
        if winner == OPPONENT: return -WIN_SCORE, None
        return 0, None # Draw has a score of 0

    if depth == 0: # Depth limit reached, evaluate the current state heuristically
        return evaluate(board), None

    empty_cells = get_empty_cells(board)
    if not empty_cells: # Should be caught by is_game_over, but as a safeguard
        return 0, None # Draw

    best_move_for_this_level = None
    
    if maximizing_player: # ME's turn: maximize score
        max_eval = -math.inf
        for r, c in empty_cells:
            board[r][c] = ME # Make the move
            eval, _ = minimax(board, depth - 1, False, alpha, beta)
            board[r][c] = EMPTY # Undo the move (backtrack)
            
            if eval > max_eval:
                max_eval = eval
                best_move_for_this_level = (r, c)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break # Alpha-beta pruning
        return max_eval, best_move_for_this_level
    else: # OPPONENT's turn: minimize score
        min_eval = math.inf
        for r, c in empty_cells:
            board[r][c] = OPPONENT # Make the move
            eval, _ = minimax(board, depth - 1, True, alpha, beta)
            board[r][c] = EMPTY # Undo the move (backtrack)
            
            if eval < min_eval:
                min_eval = eval
                best_move_for_this_level = (r, c)
            beta = min(beta, eval)
            if beta <= alpha:
                break # Alpha-beta pruning
        return min_eval, best_move_for_this_level

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Determines the next move for the AI player (ME).
    """
    num_empty_cells = sum(row.count(EMPTY) for row in board)
    
    # Adjust search depth dynamically: deeper search when fewer moves remain
    max_search_depth = 4 # Base depth for early game
    if num_empty_cells <= 10: # Around mid-game
        max_search_depth = 5
    if num_empty_cells <= 6: # Approaching end-game
        max_search_depth = 6
    if num_empty_cells <= 4: # Very close to terminal state
        max_search_depth = num_empty_cells # Search to actual end of game

    empty_cells = get_empty_cells(board)

    # Special handling for the very first move to avoid deep search when many moves are equally good
    if num_empty_cells == BOARD_SIZE * BOARD_SIZE:
        # A center cell is often a strong opening move in Tic-Tac-Toe variants
        return (1, 1)

    # Find the best move using the Minimax algorithm with Alpha-Beta pruning
    _, best_move = minimax(board, max_search_depth, True, -math.inf, math.inf)
    
    # Fallback in case minimax unexpectedly returns None (e.g., no valid moves, or a bug)
    if best_move is None:
        if empty_cells:
            return empty_cells[0] # Return the first available empty cell
        else:
            # This scenario should ideally not happen if the game engine correctly
            # only queries for a move when one is possible.
            # Returning (0,0) as a last resort, but it implies a problem.
            return (0, 0)
    
    return best_move

