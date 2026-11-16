
import numpy as np
from collections import deque
import random

def policy(board):
    # Convert board to numpy array for easier manipulation
    board = np.array(board)
    
    # Get all legal moves
    legal_moves = get_legal_moves(board)
    
    if not legal_moves:
        return "0,0:0,0"  # Should not happen in valid game state
    
    # If only one legal move, return it
    if len(legal_moves) == 1:
        return format_move(legal_moves[0])
    
    # Use minimax to find best move
    best_move = minimax_root(board, depth=2, maximizing_player=True)
    
    return format_move(best_move)

def format_move(move):
    """Format a move tuple into the required string format"""
    from_row, from_col, to_row, to_col = move
    return f"{from_row},{from_col}:{to_row},{to_col}"

def get_legal_moves(board):
    """Get all legal moves for the current player (1)"""
    legal_moves = []
    
    for row in range(8):
        for col in range(8):
            if board[row, col] == 1:  # Current player's piece
                # Try all 8 directions
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0:
                            continue
                        
                        # Calculate distance based on pieces in line
                        distance = count_pieces_in_direction(board, row, col, dr, dc)
                        
                        if distance > 0:
                            new_row = row + dr * distance
                            new_col = col + dc * distance
                            
                            # Check if move is within bounds
                            if 0 <= new_row < 8 and 0 <= new_col < 8:
                                # Check if path is clear (no enemy pieces in the way)
                                if is_path_clear(board, row, col, new_row, new_col, dr, dc):
                                    legal_moves.append((row, col, new_row, new_col))
    
    return legal_moves

def count_pieces_in_direction(board, row, col, dr, dc):
    """Count pieces in a given direction from a position"""
    count = 0
    r, c = row + dr, col + dc
    
    while 0 <= r < 8 and 0 <= c < 8:
        if board[r, c] != 0:  # Count both player's and opponent's pieces
            count += 1
        r += dr
        c += dc
    
    return count

def is_path_clear(board, from_row, from_col, to_row, to_col, dr, dc):
    """Check if the path from (from_row, from_col) to (to_row, to_col) is clear"""
    r, c = from_row + dr, from_col + dc
    
    while (r, c) != (to_row, to_col):
        if board[r, c] == -1:  # Enemy piece blocks the path
            return False
        r += dr
        c += dc
    
    return True

def evaluate_board(board):
    """Evaluate the board state"""
    # Count connected components for each player
    my_components = count_connected_components(board, 1)
    opponent_components = count_connected_components(board, -1)
    
    # Count pieces for each player
    my_pieces = np.sum(board == 1)
    opponent_pieces = np.sum(board == -1)
    
    # Calculate mobility (number of legal moves)
    my_moves = len(get_legal_moves(board))
    # For opponent mobility, we need to check from their perspective
    opponent_moves = len(get_legal_moves(-board))
    
    # Center control
    center_score = calculate_center_control(board)
    
    # Connectivity is the most important factor
    connectivity_score = opponent_components - my_components
    
    # Mobility score
    mobility_score = my_moves - opponent_moves * 0.5
    
    # Piece count (avoid unnecessary captures unless beneficial)
    piece_score = my_pieces - opponent_pieces * 0.1
    
    # Combine scores
    total_score = (connectivity_score * 10 + 
                   mobility_score * 1 + 
                   center_score * 0.5 + 
                   piece_score * 0.1)
    
    return total_score

def count_connected_components(board, player):
    """Count connected components for a player"""
    visited = np.zeros((8, 8), dtype=bool)
    components = 0
    
    def dfs(r, c):
        """Depth-first search to find connected component"""
        if (r < 0 or r >= 8 or c < 0 or c >= 8 or 
            visited[r, c] or board[r, c] != player):
            return
        
        visited[r, c] = True
        # Check all 8 directions
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr != 0 or dc != 0:
                    dfs(r + dr, c + dc)
    
    for r in range(8):
        for c in range(8):
            if board[r, c] == player and not visited[r, c]:
                dfs(r, c)
                components += 1
    
    return components

def calculate_center_control(board):
    """Calculate center control score"""
    center_weights = np.array([
        [1, 2, 3, 3, 3, 3, 2, 1],
        [2, 3, 4, 4, 4, 4, 3, 2],
        [3, 4, 5, 5, 5, 5, 4, 3],
        [3, 4, 5, 6, 6, 5, 4, 3],
        [3, 4, 5, 6, 6, 5, 4, 3],
        [3, 4, 5, 5, 5, 5, 4, 3],
        [2, 3, 4, 4, 4, 4, 3, 2],
        [1, 2, 3, 3, 3, 3, 2, 1]
    ])
    
    return np.sum(board * center_weights)

def make_move(board, move):
    """Make a move on the board and return the new board state"""
    from_row, from_col, to_row, to_col = move
    new_board = board.copy()
    
    # Move piece
    new_board[to_row, to_col] = new_board[from_row, from_col]
    new_board[from_row, from_col] = 0
    
    # Capture opponent piece if present
    if new_board[to_row, to_col] == 1 and board[to_row, to_col] == -1:
        new_board[to_row, to_col] = 1
    
    return new_board

def minimax_root(board, depth, maximizing_player):
    """Root function for minimax with alpha-beta pruning"""
    legal_moves = get_legal_moves(board)
    
    if maximizing_player:
        best_value = float('-inf')
        best_move = legal_moves[0]
        
        for move in legal_moves:
            new_board = make_move(board, move)
            value = minimax(new_board, depth - 1, float('-inf'), float('inf'), False)
            
            if value > best_value:
                best_value = value
                best_move = move
        
        return best_move
    else:
        best_value = float('inf')
        best_move = legal_moves[0]
        
        for move in legal_moves:
            new_board = make_move(board, move)
            value = minimax(new_board, depth - 1, float('-inf'), float('inf'), True)
            
            if value < best_value:
                best_value = value
                best_move = move
        
        return best_move

def minimax(board, depth, alpha, beta, maximizing_player):
    """Minimax algorithm with alpha-beta pruning"""
    if depth == 0 or is_game_over(board):
        return evaluate_board(board)
    
    legal_moves = get_legal_moves(board)
    
    if maximizing_player:
        max_eval = float('-inf')
        for move in legal_moves:
            new_board = make_move(board, move)
            eval_val = minimax(new_board, depth - 1, alpha, beta, False)
            max_eval = max(max_eval, eval_val)
            alpha = max(alpha, eval_val)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in legal_moves:
            new_board = make_move(board, move)
            eval_val = minimax(new_board, depth - 1, alpha, beta, True)
            min_eval = min(min_eval, eval_val)
            beta = min(beta, eval_val)
            if beta <= alpha:
                break
        return min_eval

def is_game_over(board):
    """Check if the game is over (either player has won)"""
    my_components = count_connected_components(board, 1)
    opponent_components = count_connected_components(board, -1)
    
    return my_components == 1 or opponent_components == 1
