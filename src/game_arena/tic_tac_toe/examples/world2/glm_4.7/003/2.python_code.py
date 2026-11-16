
import math
from typing import List, Tuple

# Precompute winning lines (indices)
LINES = []
# Rows
for r in range(4):
    LINES.append([(r, c) for c in range(4)])
# Columns
for c in range(4):
    LINES.append([(r, c) for r in range(4)])
# Diagonals
LINES.append([(i, i) for i in range(4)])
LINES.append([(i, 3 - i) for i in range(4)])

def check_winner(board: List[List[int]]) -> int:
    """Returns 1 if player 1 wins, -1 if player -1 wins, 0 otherwise."""
    for line in LINES:
        values = [board[r][c] for r, c in line]
        if all(v == 1 for v in values):
            return 1
        if all(v == -1 for v in values):
            return -1
    return 0

def evaluate(board: List[List[int]]) -> int:
    """Heuristic evaluation of the board state."""
    score = 0
    # Weights for lines with 0, 1, 2, 3, or 4 marks
    weights = [0, 1, 10, 1000, 100000]
    
    for line in LINES:
        values = [board[r][c] for r, c in line]
        p1_count = values.count(1)
        p2_count = values.count(-1)
        
        # If a line has both players' marks, it is dead (useless)
        if p1_count > 0 and p2_count > 0:
            continue
            
        score += weights[p1_count]
        score -= weights[p2_count]
        
    return score

def get_available_moves(board: List[List[int]]) -> List[Tuple[int, int]]:
    moves = []
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                moves.append((r, c))
    return moves

def order_moves(moves: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """Sort moves to improve alpha-beta pruning efficiency (Center > Corners > Edges)."""
    center = {(1, 1), (1, 2), (2, 1), (2, 2)}
    corners = {(0, 0), (0, 3), (3, 0), (3, 3)}
    
    def priority(move):
        if move in center: return 2
        if move in corners: return 1
        return 0
        
    return sorted(moves, key=priority, reverse=True)

def minimax(board: List[List[int]], depth: int, alpha: float, beta: float, is_maximizing: bool) -> int:
    winner = check_winner(board)
    if winner == 1: return 100000 - depth # Prefer faster wins
    if winner == -1: return -100000 + depth # Prefer slower losses
    if depth == 0: return evaluate(board)
    
    available_moves = get_available_moves(board)
    if not available_moves:
        return 0 # Draw

    sorted_moves = order_moves(available_moves)

    if is_maximizing:
        max_eval = -math.inf
        for r, c in sorted_moves:
            board[r][c] = 1
            eval_score = minimax(board, depth - 1, alpha, beta, False)
            board[r][c] = 0
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = math.inf
        for r, c in sorted_moves:
            board[r][c] = -1
            eval_score = minimax(board, depth - 1, alpha, beta, True)
            board[r][c] = 0
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Determines the next move for a 4x4 Tic Tac Toe game.
    Uses Minimax with Alpha-Beta pruning.
    """
    # If board is empty, take a central square
    if not any(any(row) for row in board):
        return (1, 1)
        
    available_moves = get_available_moves(board)
    if not available_moves:
        return (0, 0) # Should not happen in a valid game state

    # Dynamic depth based on number of empty squares
    # 16 total squares.
    num_empty = len(available_moves)
    
    depth = 6
    if num_empty < 10: depth = 8
    if num_empty < 6: depth = 11
    if num_empty < 4: depth = 15 # Solve endgame

    best_score = -math.inf
    best_move = available_moves[0]
    
    alpha = -math.inf
    beta = math.inf
    
    sorted_moves = order_moves(available_moves)
    
    for r, c in sorted_moves:
        board[r][c] = 1
        score = minimax(board, depth - 1, alpha, beta, False)
        board[r][c] = 0
        
        if score > best_score:
            best_score = score
            best_move = (r, c)
        
        alpha = max(alpha, score)
        
        # Prune if we found a winning move
        if score >= 100000:
            break
            
    return best_move
