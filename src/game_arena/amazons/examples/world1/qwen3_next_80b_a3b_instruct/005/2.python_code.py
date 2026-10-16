
import numpy as np
import time
from typing import List, Tuple, Optional

# Define directions: 8 directions a queen can move
DIRECTIONS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1)
]

def is_within_bounds(r: int, c: int) -> bool:
    return 0 <= r < 6 and 0 <= c < 6

def is_empty_or_vacated(board, r, c, from_r, from_c):
    """Check if square (r,c) is empty or is the vacated 'from' square."""
    if (r, c) == (from_r, from_c):
        return True  # Vacated square is now free
    return board[r, c] == 0

def get_moves_from(board, r, c, player=1):
    """Get all possible move-to squares from (r,c) for a player's amazon."""
    moves = []
    for dr, dc in DIRECTIONS:
        step = 1
        while True:
            nr, nc = r + dr * step, c + dc * step
            if not is_within_bounds(nr, nc):
                break
            # Can only move to empty squares (0) or the vacated square (but vacated is not relevant here since we're moving FROM (r,c))
            if not is_empty_or_vacated(board, nr, nc, r, c):
                break
            moves.append((nr, nc))
            step += 1
    return moves

def get_arrow_shots_from(board, r, c, from_r, from_c):
    """Get all possible arrow shooting positions from (r,c) after moving there, considering vacated from square."""
    arrows = []
    for dr, dc in DIRECTIONS:
        step = 1
        while True:
            nr, nc = r + dr * step, c + dc * step
            if not is_within_bounds(nr, nc):
                break
            # Can shoot through vacated square, but not through any blocker (1,2,-1) except possibly the vacated square
            if not is_empty_or_vacated(board, nr, nc, from_r, from_c):
                break
            arrows.append((nr, nc))
            step += 1
    return arrows

def get_all_legal_moves(board, player=1):
    """Return list of all legal moves: (from_r, from_c, to_r, to_c, arrow_r, arrow_c)"""
    moves = []
    # Find all amazons of current player
    for r in range(6):
        for c in range(6):
            if board[r, c] == player:
                # Get all possible to-squares
                to_squares = get_moves_from(board, r, c, player)
                for to_r, to_c in to_squares:
                    # From the new position, get all possible arrow shots
                    arrow_squares = get_arrow_shots_from(board, to_r, to_c, r, c)
                    for arrow_r, arrow_c in arrow_squares:
                        moves.append((r, c, to_r, to_c, arrow_r, arrow_c))
    return moves

def simulate_move(board, move):
    """Return a new board after applying the move."""
    from_r, from_c, to_r, to_c, arrow_r, arrow_c = move
    new_board = board.copy()
    # Move amazon: vacate from, occupy to
    new_board[from_r, from_c] = 0
    new_board[to_r, to_c] = 1
    # Shoot arrow
    new_board[arrow_r, arrow_c] = -1
    return new_board

def count_mobility(board, player):
    """Count total legal moves for the player on the board."""
    moves = get_all_legal_moves(board, player)
    return len(moves)

def evaluate_board(board):
    """Heuristic evaluation function for the current board state."""
    # Count mobility for both players
    my_mobility = count_mobility(board, 1)
    opp_mobility = count_mobility(board, 2)
    
    # Central control: score positions near center
    center_bonus = [
        [0, 0, 1, 1, 0, 0],
        [0, 1, 2, 2, 1, 0],
        [1, 2, 3, 3, 2, 1],
        [1, 2, 3, 3, 2, 1],
        [0, 1, 2, 2, 1, 0],
        [0, 0, 1, 1, 0, 0]
    ]
    
    my_center_score = 0
    opp_center_score = 0
    
    for r in range(6):
        for c in range(6):
            if board[r, c] == 1:
                my_center_score += center_bonus[r][c]
            elif board[r, c] == 2:
                opp_center_score += center_bonus[r][c]
    
    # Avoid positions near the edge if possible (but center is more important)
    # Penalize being surrounded: add a small penalty if amazons are on edge
    edge_penalty = 0
    for r in range(6):
        for c in range(6):
            if board[r, c] == 1:
                if r in [0,5] or c in [0,5]:
                    edge_penalty += 0.1
    
    # Primary factor: mobility difference
    mobility_score = my_mobility - opp_mobility
    
    # Return weighted combination
    # Mobility is most important, then center control
    return mobility_score * 10 + (my_center_score - opp_center_score) * 2 - edge_penalty

def minimax(board, depth, alpha, beta, maximizing_player, start_time, time_limit=0.95):
    """
    Minimax with alpha-beta pruning and time limit.
    Returns: (score, best_move)
    """
    if time.time() - start_time > time_limit:
        return 0, None  # Timeout, return dummy

    legal_moves = get_all_legal_moves(board, 1 if maximizing_player else 2)
    
    if depth == 0 or len(legal_moves) == 0:
        return evaluate_board(board), None

    if maximizing_player:
        max_eval = -float('inf')
        best_move = None
        # Sort moves by heuristic to improve pruning
        scored_moves = [(move, evaluate_board(simulate_move(board, move))) for move in legal_moves]
        scored_moves.sort(key=lambda x: x[1], reverse=True)
        
        for move, _ in scored_moves:
            new_board = simulate_move(board, move)
            eval_score, _ = minimax(new_board, depth - 1, alpha, beta, False, start_time, time_limit)
            if eval_score is None:  # Timeout
                return None, None
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        best_move = None
        # Sort moves by heuristic (opponent wants to minimize)
        scored_moves = [(move, evaluate_board(simulate_move(board, move))) for move in legal_moves]
        scored_moves.sort(key=lambda x: x[1])
        
        for move, _ in scored_moves:
            new_board = simulate_move(board, move)
            eval_score, _ = minimax(new_board, depth - 1, alpha, beta, True, start_time, time_limit)
            if eval_score is None:  # Timeout
                return None, None
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval, best_move

def policy(board) -> str:
    """
    Main policy function: returns the best move as a formatted string.
    Uses iterative deepening with alpha-beta pruning.
    """
    start_time = time.time()
    
    # If no legal moves exist, return dummy move (should not occur, but safety)
    legal_moves = get_all_legal_moves(board, 1)
    if len(legal_moves) == 0:
        # Fallback: scan for any possible move (should not happen)
        for r in range(6):
            for c in range(6):
                if board[r, c] == 1:
                    for dr, dc in DIRECTIONS:
                        nr, nc = r + dr, c + dc
                        if is_within_bounds(nr, nc) and board[nr, nc] == 0:
                            # Try to shoot arrow in same direction
                            ar, ac = nr + dr, nc + dc
                            if is_within_bounds(ar, ac) and board[ar, ac] == 0:
                                return f"{r},{c}:{nr},{nc}:{ar},{ac}"
        # If still nothing, return any arbitrary legal move (should never happen)
        return "0,0:1,1:2,2"
    
    # Iterative deepening: start at depth 2 and increase until time limit
    best_move = legal_moves[0]  # fallback
    max_depth = 5  # Maximum depth we hope to reach
    
    for depth in range(2, max_depth + 1):
        if time.time() - start_time > 0.85:  # Leave buffer
            break
        score, move = minimax(board, depth, -float('inf'), float('inf'), True, start_time, 0.90)
        if move is not None and time.time() - start_time < 0.95:
            best_move = move
        else:
            # If minimax returns None (timeout), use current best
            break
    
    # Format move: "from_row,from_col:to_row,to_col:arrow_row,arrow_col"
    from_r, from_c, to_r, to_c, arrow_r, arrow_c = best_move
    return f"{from_r},{from_c}:{to_r},{to_c}:{arrow_r},{arrow_c}"
