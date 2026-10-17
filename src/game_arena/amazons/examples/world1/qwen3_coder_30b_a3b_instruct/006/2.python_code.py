
import numpy as np
import copy
from collections import deque

# Directions for queen-like movement (8 directions)
DIRECTIONS = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]

def is_valid_pos(row, col):
    """Check if position is within board bounds"""
    return 0 <= row < 6 and 0 <= col < 6

def get_all_amazon_positions(board, player):
    """Get all positions of player's amazons"""
    positions = []
    for i in range(6):
        for j in range(6):
            if board[i][j] == player:
                positions.append((i, j))
    return positions

def get_valid_moves_for_amazon(board, from_row, from_col):
    """Get all valid moves for a single amazon"""
    moves = []
    # Check each possible direction
    for dr, dc in DIRECTIONS:
        r, c = from_row + dr, from_col + dc
        # Move in this direction until we hit a boundary, blocker, or end
        while is_valid_pos(r, c) and board[r][c] == 0:
            moves.append((r, c))
            r += dr
            c += dc
        # If we hit a blocker or boundary, we stop in this direction
    return moves

def get_valid_arrow_positions(board, from_row, from_col, to_row, to_col):
    """Get all valid arrow positions from a landing square"""
    # Note: from_row/to_row and from_col/to_col represent the moved amazon
    # The arrow is shot from the new position (to_row, to_col)
    arrow_positions = []
    
    # Check each possible direction
    for dr, dc in DIRECTIONS:
        r, c = to_row + dr, to_col + dc
        # Arrow can be shot in any direction, can be any distance, must go unobstructed
        while is_valid_pos(r, c):
            if board[r][c] == 0:  # Empty square
                arrow_positions.append((r, c))
            elif board[r][c] == -1 or board[r][c] == 1 or board[r][c] == 2:
                # Arrow cannot land on anything - it's blocked
                break
            r += dr
            c += dc
    return arrow_positions

def get_all_legal_moves(board):
    """Get all legal moves in the current position"""
    legal_moves = []
    
    # Get all my amazons
    my_amazons = get_all_amazon_positions(board, 1)
    
    for from_row, from_col in my_amazons:
        # Get all possible moves from this amazon
        moves = get_valid_moves_for_amazon(board, from_row, from_col)
        for to_row, to_col in moves:
            # Get all valid arrow positions from the new square
            arrows = get_valid_arrow_positions(board, from_row, from_col, to_row, to_col)
            for arrow_row, arrow_col in arrows:
                legal_moves.append((from_row, from_col, to_row, to_col, arrow_row, arrow_col))
    
    return legal_moves

def apply_move(board, from_row, from_col, to_row, to_col, arrow_row, arrow_col):
    """Apply a move and return a new board state"""
    new_board = copy.deepcopy(board)
    # Move the amazon
    new_board[from_row][from_col] = 0
    new_board[to_row][to_col] = 1
    # Place the arrow
    new_board[arrow_row][arrow_col] = -1
    return new_board

def evaluate_board(board):
    """Evaluate the board position"""
    score = 0
    
    # Check for terminal positions (no moves left)
    my_moves = get_all_legal_moves(board)
    if len(my_moves) == 0:
        # No moves left - opponent wins
        return -10000
    # Opponent has no moves - I win
    # We are trying to maximize, so we should prefer positions where I have moves
    # For now, just count the legal moves as one factor
    score += len(my_moves) * 100
    
    # Evaluate central control
    center = [(2,2), (2,3), (3,2), (3,3)]
    my_amazons = get_all_amazon_positions(board, 1)
    opponent_amazons = get_all_amazon_positions(board, 2)
    
    # Prefer controlling center positions
    for r, c in center:
        if board[r][c] == 0:  # Empty center
            for mr, mc in my_amazons:
                # Calculate Manhattan distance to center
                distance = abs(r - mr) + abs(c - mc)
                score += (8 - distance)  # Closer to center = better for me
    
    # Prefer mobility (more potential moves)
    my_amazons = get_all_amazon_positions(board, 1)
    opponent_amazons = get_all_amazon_positions(board, 2)
    
    # Count how many moves each side has
    my_total_moves = 0
    for r, c in my_amazons:
        my_total_moves += len(get_valid_moves_for_amazon(board, r, c))
    
    opponent_total_moves = 0
    for r, c in opponent_amazons:
        opponent_total_moves += len(get_valid_moves_for_amazon(board, r, c))
    
    # We want to maximize our moves and minimize opponent's moves
    score += (my_total_moves - opponent_total_moves) * 50
    
    # Prefer fewer arrows - more open spaces
    arrow_count = np.sum(board == -1)
    score -= arrow_count * 10
    
    return score

def minimax(board, depth, alpha, beta, maximizing_player):
    """Minimax with alpha-beta pruning"""
    if depth == 0:
        return evaluate_board(board)
    
    if maximizing_player:
        max_eval = float('-inf')
        legal_moves = get_all_legal_moves(board)
        for move in legal_moves:
            from_row, from_col, to_row, to_col, arrow_row, arrow_col = move
            new_board = apply_move(board, from_row, from_col, to_row, to_col, arrow_row, arrow_col)
            eval_score = minimax(new_board, depth - 1, alpha, beta, False)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        legal_moves = get_all_legal_moves(board)
        for move in legal_moves:
            from_row, from_col, to_row, to_col, arrow_row, arrow_col = move
            new_board = apply_move(board, from_row, from_col, to_row, to_col, arrow_row, arrow_col)
            eval_score = minimax(new_board, depth - 1, alpha, beta, True)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval

def policy(board):
    """Main policy function to return the next move"""
    legal_moves = get_all_legal_moves(board)
    
    if not legal_moves:
        return None
    
    # Use minimax to choose the best move
    best_move = None
    best_score = float('-inf')
    alpha = float('-inf')
    beta = float('inf')
    
    # Limit depth for performance
    max_depth = 3
    
    for move in legal_moves:
        from_row, from_col, to_row, to_col, arrow_row, arrow_col = move
        new_board = apply_move(board, from_row, from_col, to_row, to_col, arrow_row, arrow_col)
        score = minimax(new_board, max_depth - 1, alpha, beta, False)
        if score > best_score:
            best_score = score
            best_move = (from_row, from_col, to_row, to_col, arrow_row, arrow_col)
            
        # For move ordering, we can sort moves based on some heuristic here
        # But for now just process in order
    
    if best_move is None:
        # Fallback to first legal move
        from_row, from_col, to_row, to_col, arrow_row, arrow_col = legal_moves[0]
        return f"{from_row},{from_col}:{to_row},{to_col}:{arrow_row},{arrow_col}"
    
    from_row, from_col, to_row, to_col, arrow_row, arrow_col = best_move
    return f"{from_row},{from_col}:{to_row},{to_col}:{arrow_row},{arrow_col}"
