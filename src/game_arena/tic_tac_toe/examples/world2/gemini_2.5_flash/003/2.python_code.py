
import math
import copy

# Global constants for readability
BOARD_SIZE = 4
ME = 1
OPPONENT = -1
EMPTY = 0

# Score values for evaluation function
WIN_SCORE = 1000000  # High score for winning
LOSE_SCORE = -1000000 # Low score for losing
THREE_IN_A_ROW_OPP = -10000 # Opponent has 3 in a row, needs block
THREE_IN_A_ROW_ME = 10000 # I have 3 in a row, potential win
TWO_IN_A_ROW_OPP = -100 # Opponent has 2 in a row
TWO_IN_A_ROW_ME = 100 # I have 2 in a row
CENTER_BONUS = 50 # Bonus for owning a center square

# Max depth for minimax search.
# 6 seems like a good balance for 4x4 within typical 1-second timeout.
# Deeper search implies more time, shallower less optimal moves.
MAX_DEPTH = 6

# Pre-calculate all 4-cell lines on the board for efficiency
ALL_LINES = []
# Rows
for r in range(BOARD_SIZE):
    ALL_LINES.append([(r, c) for c in range(BOARD_SIZE)])
# Columns
for c in range(BOARD_SIZE):
    ALL_LINES.append([(r, c) for r in range(BOARD_SIZE)])
# Main diagonal
ALL_LINES.append([(i, i) for i in range(BOARD_SIZE)])
# Anti-diagonal
ALL_LINES.append([(i, BOARD_SIZE - 1 - i) for i in range(BOARD_SIZE)])


def check_for_winner(board: list[list[int]]) -> int:
    """
    Checks if there's a winner on the given board.
    Returns ME if I win, OPPONENT if opponent wins, 0 if no winner yet.
    """
    for line in ALL_LINES:
        current_sum = 0
        for r, c in line:
            current_sum += board[r][c]
        if current_sum == BOARD_SIZE * ME:
            return ME
        if current_sum == BOARD_SIZE * OPPONENT:
            return OPPONENT
    return EMPTY

def get_possible_moves(board: list[list[int]]) -> list[tuple[int, int]]:
    """
    Returns a list of all empty cells (r, c) as possible moves.
    """
    moves = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == EMPTY:
                moves.append((r, c))
    return moves

def evaluate_board(board: list[list[int]]) -> int:
    """
    Evaluates the current state of the board.
    Positive score means good for ME, negative is good for OPPONENT.
    """
    winner = check_for_winner(board)
    if winner == ME:
        return WIN_SCORE
    if winner == OPPONENT:
        return LOSE_SCORE

    score = 0

    # Heuristics based on lines
    for line in ALL_LINES:
        my_pieces = 0
        opp_pieces = 0
        empty_pieces = 0

        for r, c in line:
            if board[r][c] == ME:
                my_pieces += 1
            elif board[r][c] == OPPONENT:
                opp_pieces += 1
            else:
                empty_pieces += 1

        # Evaluate based on patterns in the line
        if my_pieces == 3 and empty_pieces == 1:
            score += THREE_IN_A_ROW_ME # My potential win (high priority)
        elif opp_pieces == 3 and empty_pieces == 1:
            score += THREE_IN_A_ROW_OPP # Opponent potential win (critical block)
        elif my_pieces == 2 and empty_pieces == 2:
            score += TWO_IN_A_ROW_ME
        elif opp_pieces == 2 and empty_pieces == 2:
            score += TWO_IN_A_ROW_OPP

    # Center square bonus
    center_cells = [(1,1), (1,2), (2,1), (2,2)]
    for r, c in center_cells:
        if board[r][c] == ME:
            score += CENTER_BONUS
        elif board[r][c] == OPPONENT:
            score -= CENTER_BONUS

    return score


def minimax(board: list[list[int]], depth: int, is_maximizing_player: bool, alpha: float, beta: float) -> int:
    """
    Minimax algorithm with Alpha-Beta Pruning.
    """
    # Check for terminal states or max depth
    winner = check_for_winner(board)
    if winner == ME:
        return WIN_SCORE - depth # Subtract depth to prefer faster wins
    if winner == OPPONENT:
        return LOSE_SCORE + depth # Add depth to prefer slower losses

    possible_moves = get_possible_moves(board)
    if not possible_moves: # Draw
        return 0

    if depth == MAX_DEPTH:
        return evaluate_board(board)

    if is_maximizing_player: # AI's turn
        max_eval = -math.inf
        for r, c in possible_moves:
            new_board = [row[:] for row in board] # Deep copy
            new_board[r][c] = ME
            eval = minimax(new_board, depth + 1, False, alpha, beta)
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break # Alpha-beta pruning
        return max_eval
    else: # Opponent's turn
        min_eval = math.inf
        for r, c in possible_moves:
            new_board = [row[:] for row in board] # Deep copy
            new_board[r][c] = OPPONENT
            eval = minimax(new_board, depth + 1, True, alpha, beta)
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break # Alpha-beta pruning
        return min_eval


def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    The main policy function to determine the best move for the AI.
    """
    best_move = None
    best_value = -math.inf
    
    available_moves = get_possible_moves(board)

    # Optimization for the very first move: take a center square directly
    if len(available_moves) == BOARD_SIZE * BOARD_SIZE: # Board is completely empty
        # Pick one of the central 2x2 squares
        return (1,1) # Example, could be any of (1,1), (1,2), (2,1), (2,2)

    for r, c in available_moves:
        new_board = [row[:] for row in board] # Deep copy
        new_board[r][c] = ME # Make the potential move for AI

        # Call minimax for the opponent's turn (False for is_maximizing_player)
        move_value = minimax(new_board, 0, False, -math.inf, math.inf)

        if move_value > best_value:
            best_value = move_value
            best_move = (r, c)
            
    # Fallback: if no best_move is found (should only happen if available_moves is empty,
    # but check for robustness)
    if best_move is None and available_moves:
        return available_moves[0] # Return the first available move

    return best_move
