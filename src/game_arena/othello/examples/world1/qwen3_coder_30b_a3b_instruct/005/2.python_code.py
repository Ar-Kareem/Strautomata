
import numpy as np
from collections import deque

def get_legal_moves(board, opponent_board, player):
    """Get all legal moves for the given player"""
    moves = []
    for r in range(8):
        for c in range(8):
            if board[r][c] == 0 and opponent_board[r][c] == 0:
                if is_legal_move(board, opponent_board, player, r, c):
                    moves.append((r, c))
    return moves

def is_legal_move(board, opponent_board, player, r, c):
    """Check if placing at (r,c) is a legal move"""
    if board[r][c] != 0 or opponent_board[r][c] != 0:
        return False
    
    directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
    
    for dr, dc in directions:
        row, col = r + dr, c + dc
        found_opponent = False
        
        while 0 <= row < 8 and 0 <= col < 8:
            if opponent_board[row][col] == player:
                if found_opponent:
                    return True
                break
            elif board[row][col] == player:
                break
            else:
                found_opponent = True
            row += dr
            col += dc
    
    return False

def get_flipped_discs(board, opponent_board, player, r, c):
    """Get all discs that would be flipped if placing at (r,c)"""
    flipped = set()
    directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
    
    for dr, dc in directions:
        row, col = r + dr, c + dc
        to_flip = []
        found_opponent = False
        
        while 0 <= row < 8 and 0 <= col < 8:
            if opponent_board[row][col] == player:
                if found_opponent:
                    flipped.update(to_flip)
                    break
                break
            elif board[row][col] == player:
                break
            else:
                to_flip.append((row, col))
                found_opponent = True
            row += dr
            col += dc
    
    return flipped

def make_move(board, opponent_board, player, r, c):
    """Make a move and return new boards"""
    new_board = board.copy()
    new_opponent_board = opponent_board.copy()
    
    # Place the disc
    new_board[r][c] = player
    
    # Flip discs
    flipped = get_flipped_discs(board, opponent_board, player, r, c)
    for row, col in flipped:
        new_opponent_board[row][col] = 0
        new_board[row][col] = player
    
    return new_board, new_opponent_board

def evaluate_position(board, opponent_board):
    """Simple static evaluation function"""
    # Count discs
    player_count = np.sum(board)
    opponent_count = np.sum(opponent_board)
    
    # Mobility evaluation
    player_moves = len(get_legal_moves(board, opponent_board, 1))
    opponent_moves = len(get_legal_moves(opponent_board, board, 0))
    
    # Corner control
    corners = [(0,0), (0,7), (7,0), (7,7)]
    player_corners = sum(1 for r, c in corners if board[r][c] == 1)
    opponent_corners = sum(1 for r, c in corners if opponent_board[r][c] == 1)
    
    # Edge stability
    edges = []
    for i in range(8):
        edges.append((0, i))  # Top edge
        edges.append((7, i))  # Bottom edge
        edges.append((i, 0))  # Left edge
        edges.append((i, 7))  # Right edge
    
    player_edge = sum(1 for r, c in edges if board[r][c] == 1)
    opponent_edge = sum(1 for r, c in edges if opponent_board[r][c] == 1)
    
    # Weighted evaluation
    mobility_score = player_moves - opponent_moves
    corner_score = player_corners - opponent_corners
    edge_score = player_edge - opponent_edge
    disc_score = player_count - opponent_count
    
    score = 10 * corner_score + 2 * edge_score + 2 * mobility_score + disc_score
    
    return score

def minimax(board, opponent_board, depth, max_player, alpha, beta):
    """Minimax search with alpha-beta pruning"""
    if depth == 0:
        return evaluate_position(board, opponent_board)
    
    legal_moves = get_legal_moves(board, opponent_board, 1 if max_player else 0)
    if not legal_moves:
        # No moves available, switch players
        if depth == 3:
            return evaluate_position(board, opponent_board)
        else:
            return minimax(board, opponent_board, depth - 1, not max_player, alpha, beta)
    
    if max_player:
        max_eval = float('-inf')
        for r, c in legal_moves:
            new_board, new_opponent_board = make_move(board, opponent_board, 1, r, c)
            eval_score = minimax(new_board, new_opponent_board, depth - 1, False, alpha, beta)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for r, c in legal_moves:
            new_board, new_opponent_board = make_move(board, opponent_board, 0, r, c)
            eval_score = minimax(new_board, new_opponent_board, depth - 1, True, alpha, beta)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    legal_moves = get_legal_moves(you, opponent, 1)
    
    if not legal_moves:
        return "pass"
    
    # Use a more aggressive approach with simple heuristics first
    # Try to prioritize corners as they're most stable
    corners = [(0,0), (0,7), (7,0), (7,7)]
    for r, c in corners:
        if (r, c) in legal_moves:
            return chr(ord('a') + c) + str(8 - r)
    
    # Try to avoid edges where possible
    edge_positions = []    # Positions along outer edges but not corners
    for i in range(1, 7):
        edge_positions.extend([(0, i), (7, i), (i, 0), (i, 7)])
    
    # Try to find moves that give us mobility and avoid opponent mobility
    best_move = None
    best_score = float('-inf')
    
    # Try different moves and evaluate them using our heuristic
    for r, c in legal_moves:
        board_copy = you.copy()
        opponent_copy = opponent.copy()
        
        # Make a move to simulate
        new_board, new_opponent_board = make_move(board_copy, opponent_copy, 1, r, c)
        
        # Evaluate
        score = evaluate_position(new_board, new_opponent_board)
        
        if score > best_score:
            best_score = score
            best_move = (r, c)
    
    if best_move is None:
        r, c = legal_moves[0]  # Fallback to first valid move
        return chr(ord('a') + c) + str(8 - r)
    
    r, c = best_move
    return chr(ord('a') + c) + str(8 - r)
