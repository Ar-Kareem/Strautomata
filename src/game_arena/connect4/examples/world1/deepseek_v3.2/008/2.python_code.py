
import numpy as np
from copy import deepcopy

# Precompute all winning lines (4 positions) for a 6x7 board
WINNING_LINES = []

# Horizontal lines
for r in range(6):
    for c in range(4):
        WINNING_LINES.append([(r, c + i) for i in range(4)])

# Vertical lines
for c in range(7):
    for r in range(3):
        WINNING_LINES.append([(r + i, c) for i in range(4)])

# Diagonal down-right
for r in range(3):
    for c in range(4):
        WINNING_LINES.append([(r + i, c + i) for i in range(4)])

# Diagonal down-left
for r in range(3):
    for c in range(3, 7):
        WINNING_LINES.append([(r + i, c - i) for i in range(4)])

def check_win(board, player):
    """Check if player has won."""
    for line in WINNING_LINES:
        if all(board[r][c] == player for r, c in line):
            return True
    return False

def get_valid_moves(board):
    """Return list of columns that are not full."""
    return [c for c in range(7) if board[0][c] == 0]

def make_move(board, col, player):
    """Return a new board after player drops a disc in column col."""
    new_board = deepcopy(board)
    for row in range(5, -1, -1):
        if new_board[row][col] == 0:
            new_board[row][col] = player
            break
    return new_board

def evaluate_board(board):
    """
    Evaluate the board from the perspective of player 1 (us).
    Higher score is better for us.
    """
    score = 0
    # Prefer center column
    center_col = 3
    for r in range(6):
        if board[r][center_col] == 1:
            score += 3
        elif board[r][center_col] == -1:
            score -= 3
    
    # Evaluate winning lines
    for line in WINNING_LINES:
        ours = 0
        opps = 0
        for r, c in line:
            if board[r][c] == 1:
                ours += 1
            elif board[r][c] == -1:
                opps += 1
        
        if ours > 0 and opps > 0:
            # Line is blocked for both, no threat
            continue
        elif ours > 0:
            # Only our discs
            if ours == 3:
                score += 100  # Very close to win
            elif ours == 2:
                score += 10
            elif ours == 1:
                score += 1
        elif opps > 0:
            # Only opponent discs
            if opps == 3:
                score -= 1000  # Immediate threat, but should be blocked before evaluation
            elif opps == 2:
                score -= 10
            elif opps == 1:
                score -= 1
    
    return score

def negamax(board, depth, alpha, beta, player):
    """
    Negamax implementation with alpha-beta pruning.
    Player: 1 for us, -1 for opponent.
    Returns (score, best_move_column).
    """
    valid_moves = get_valid_moves(board)
    
    # Check for terminal states
    if check_win(board, 1):
        return (1000000, None)
    if check_win(board, -1):
        return (-1000000, None)
    if depth == 0 or not valid_moves:
        # Evaluate from perspective of player 1 (us)
        eval_score = evaluate_board(board)
        return (eval_score * player, None)  # negamax: score from current player's view
    
    best_score = -float('inf')
    best_col = valid_moves[0]
    
    for col in valid_moves:
        new_board = make_move(board, col, player)
        score, _ = negamax(new_board, depth - 1, -beta, -alpha, -player)
        score = -score  # negamax: flip sign
        
        if score > best_score:
            best_score = score
            best_col = col
        
        alpha = max(alpha, best_score)
        if alpha >= beta:
            break
    
    return (best_score, best_col)

def policy(board):
    """
    Main policy function.
    Returns the column index (0-6) to play.
    """
    # First, check if we can win immediately
    valid_moves = get_valid_moves(board)
    for col in valid_moves:
        new_board = make_move(board, col, 1)
        if check_win(new_board, 1):
            return col
    
    # Check if opponent can win next move (block)
    for col in valid_moves:
        new_board = make_move(board, col, -1)
        if check_win(new_board, -1):
            return col
    
    # Otherwise, use negamax search with depth 6
    # Adjust depth based on number of moves left for speed
    moves_left = sum(1 for r in range(6) for c in range(7) if board[r][c] == 0)
    if moves_left > 30:
        depth = 5
    elif moves_left > 20:
        depth = 6
    elif moves_left > 10:
        depth = 7
    else:
        depth = 8  # endgame, can search deeper
    
    # Ensure depth is not too high for time constraint
    depth = min(depth, 8)
    
    _, best_col = negamax(board, depth, -float('inf'), float('inf'), 1)
    return best_col
