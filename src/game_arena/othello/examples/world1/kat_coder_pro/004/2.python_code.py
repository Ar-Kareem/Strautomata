
import numpy as np
import time
from collections import defaultdict

# Direction vectors for the 8 possible directions
DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

# Corner and edge weights
CORNER_WEIGHT = 1000
EDGE_WEIGHT = 500
MOBILITY_WEIGHT = 10
DISC_WEIGHT = 1

# Transposition table for caching
transposition_table = defaultdict(lambda: (None, -np.inf, np.inf))

def is_valid_move(board, opponent_board, r, c):
    """Check if placing a disc at (r, c) is valid."""
    if board[r][c] == 1 or opponent_board[r][c] == 1:
        return False
    
    # Check all 8 directions for possible flips
    for dr, dc in DIRECTIONS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 8 and 0 <= nc < 8 and opponent_board[nr][nc] == 1:
            # Found opponent disc, check if it leads to our disc
            while 0 <= nr < 8 and 0 <= nc < 8 and opponent_board[nr][nc] == 1:
                nr += dr
                nc += dc
            if 0 <= nr < 8 and 0 <= nc < 8 and board[nr][nc] == 1:
                return True
    return False

def get_valid_moves(board, opponent_board):
    """Get all valid moves for the current player."""
    moves = []
    for r in range(8):
        for c in range(8):
            if is_valid_move(board, opponent_board, r, c):
                moves.append((r, c))
    return moves

def make_move(board, opponent_board, r, c):
    """Make a move and return the new boards."""
    new_board = board.copy()
    new_opponent_board = opponent_board.copy()
    
    # Place the disc
    new_board[r][c] = 1
    
    # Flip opponent discs
    for dr, dc in DIRECTIONS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 8 and 0 <= nc < 8 and new_opponent_board[nr][nc] == 1:
            # Check if this direction leads to our disc
            to_flip = []
            while 0 <= nr < 8 and 0 <= nc < 8 and new_opponent_board[nr][nc] == 1:
                to_flip.append((nr, nc))
                nr += dr
                nc += dc
            if 0 <= nr < 8 and 0 <= nc < 8 and new_board[nr][nc] == 1:
                # Flip all discs in this direction
                for fr, fc in to_flip:
                    new_opponent_board[fr][fc] = 0
                    new_board[fr][fc] = 1
    
    return new_board, new_opponent_board

def evaluate(board, opponent_board):
    """Evaluate the board state."""
    score = 0
    
    # Corner control
    corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
    for r, c in corners:
        if board[r][c] == 1:
            score += CORNER_WEIGHT
        elif opponent_board[r][c] == 1:
            score -= CORNER_WEIGHT
    
    # Edge control (excluding corners)
    edges = []
    for i in range(1, 7):
        edges.extend([(0, i), (7, i), (i, 0), (i, 7)])
    
    for r, c in edges:
        if board[r][c] == 1:
            score += EDGE_WEIGHT
        elif opponent_board[r][c] == 1:
            score -= EDGE_WEIGHT
    
    # Mobility (number of valid moves)
    my_moves = len(get_valid_moves(board, opponent_board))
    opponent_moves = len(get_valid_moves(opponent_board, board))
    score += MOBILITY_WEIGHT * (my_moves - opponent_moves)
    
    # Disc count
    my_discs = np.sum(board)
    opponent_discs = np.sum(opponent_board)
    score += DISC_WEIGHT * (my_discs - opponent_discs)
    
    return score

def minimax(board, opponent_board, depth, alpha, beta, maximizing_player, start_time):
    """Minimax with alpha-beta pruning."""
    # Time limit check
    if time.time() - start_time > 0.9:
        return evaluate(board, opponent_board)
    
    # Transposition table lookup
    key = (tuple(board.flatten()), tuple(opponent_board.flatten()))
    if key in transposition_table:
        stored_depth, stored_alpha, stored_beta, stored_value = transposition_table[key]
        if stored_depth >= depth:
            if stored_alpha <= alpha and stored_beta >= beta:
                return stored_value
    
    # Get valid moves
    moves = get_valid_moves(board, opponent_board)
    
    # Terminal state (no moves for current player)
    if not moves:
        # If opponent also has no moves, game is over
        opponent_moves = get_valid_moves(opponent_board, board)
        if not opponent_moves:
            # Game over - count discs
            my_discs = np.sum(board)
            opponent_discs = np.sum(opponent_board)
            return 1000 if my_discs > opponent_discs else -1000 if opponent_discs > my_discs else 0
        # Opponent's turn
        return -minimax(opponent_board, board, depth, -beta, -alpha, not maximizing_player, start_time)
    
    if depth == 0:
        return evaluate(board, opponent_board)
    
    if maximizing_player:
        max_eval = -np.inf
        for r, c in moves:
            new_board, new_opponent_board = make_move(board, opponent_board, r, c)
            eval_score = minimax(new_board, new_opponent_board, depth - 1, alpha, beta, False, start_time)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        
        # Store in transposition table
        transposition_table[key] = (depth, alpha, beta, max_eval)
        return max_eval
    else:
        min_eval = np.inf
        for r, c in moves:
            new_board, new_opponent_board = make_move(board, opponent_board, r, c)
            eval_score = minimax(new_board, new_opponent_board, depth - 1, alpha, beta, True, start_time)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        
        # Store in transposition table
        transposition_table[key] = (depth, alpha, beta, min_eval)
        return min_eval

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """Main policy function."""
    # Clear transposition table periodically
    if np.random.random() < 0.01:  # Small chance to clear cache
        transposition_table.clear()
    
    # Get valid moves
    moves = get_valid_moves(you, opponent)
    
    if not moves:
        return "pass"
    
    # Determine search depth based on game phase
    total_discs = np.sum(you) + np.sum(opponent)
    if total_discs < 20:  # Early game
        depth = 6
    elif total_discs < 50:  # Mid game
        depth = 4
    else:  # Late game
        depth = 2
    
    # Start timing
    start_time = time.time()
    
    # Order moves by heuristic value for better pruning
    def move_heuristic(r, c):
        score = 0
        # Prioritize corners
        if (r, c) in [(0, 0), (0, 7), (7, 0), (7, 7)]:
            score += 1000
        # Prioritize edges
        elif r in [0, 7] or c in [0, 7]:
            score += 500
        return score
    
    moves.sort(key=lambda m: move_heuristic(m[0], m[1]), reverse=True)
    
    # Find best move
    best_score = -np.inf
    best_move = moves[0]
    
    for r, c in moves:
        new_board, new_opponent_board = make_move(you, opponent, r, c)
        score = minimax(new_board, new_opponent_board, depth - 1, -np.inf, np.inf, False, start_time)
        
        if score > best_score:
            best_score = score
            best_move = (r, c)
        
        # Time limit check
        if time.time() - start_time > 0.9:
            break
    
    # Convert to string format
    return chr(ord('a') + best_move[1]) + str(best_move[0] + 1)
