
import numpy as np
from collections import deque
import time
import random

def policy(board) -> str:
    """Main policy function - returns the next move."""
    board = np.array(board)
    
    # Generate all legal moves
    moves = generate_all_moves(board, 1)
    
    if not moves:
        return "0,0:0,0"
    
    # If only one move, return it
    if len(moves) == 1:
        return format_move(moves[0])
    
    # Use alpha-beta search to find best move
    best_move = alpha_beta_search(board, 1, moves)
    
    return format_move(best_move)

def format_move(move):
    """Format a move as 'from_row,from_col:to_row,to_col'."""
    return f"{move[0]},{move[1]}:{move[2]},{move[3]}"

def generate_all_moves(board, player):
    """Generate all legal moves for the given player."""
    moves = []
    for r in range(8):
        for c in range(8):
            if board[r, c] == player:
                moves.extend(get_piece_moves(board, r, c, player))
    return moves

def get_piece_moves(board, r, c, player):
    """Get all legal moves for a piece at position (r, c)."""
    moves = []
    
    # Row
    count = sum(1 for i in range(8) if board[r, i] != 0)
    moves.extend(check_move(board, r, c, 0, 1, count, player))
    moves.extend(check_move(board, r, c, 0, -1, count, player))
    
    # Column
    count = sum(1 for i in range(8) if board[i, c] != 0)
    moves.extend(check_move(board, r, c, 1, 0, count, player))
    moves.extend(check_move(board, r, c, -1, 0, count, player))
    
    # Main diagonal (\)
    diag_r, diag_c = r, c
    while diag_r > 0 and diag_c > 0:
        diag_r -= 1
        diag_c -= 1
    count = 0
    while diag_r < 8 and diag_c < 8:
        if board[diag_r, diag_c] != 0:
            count += 1
        diag_r += 1
        diag_c += 1
    moves.extend(check_move(board, r, c, 1, 1, count, player))
    moves.extend(check_move(board, r, c, -1, -1, count, player))
    
    # Anti-diagonal
    diag_r, diag_c = r, c
    while diag_r > 0 and diag_c < 7:
        diag_r -= 1
        diag_c += 1
    count = 0
    while diag_r < 8 and diag_c >= 0:
        if board[diag_r, diag_c] != 0:
            count += 1
        diag_r += 1
        diag_c -= 1
    moves.extend(check_move(board, r, c, 1, -1, count, player))
    moves.extend(check_move(board, r, c, -1, 1, count, player))
    
    return moves

def check_move(board, r, c, dr, dc, count, player):
    """Check if a move is valid and return it if so."""
    moves = []
    
    if count == 0:
        return moves
    
    # Destination
    nr, nc = r + dr * count, c + dc * count
    
    # Check bounds
    if not (0 <= nr < 8 and 0 <= nc < 8):
        return moves
    
    # Check for jumping over enemies
    for i in range(1, count):
        mr, mc = r + dr * i, c + dc * i
        if board[mr, mc] == -player:
            return moves
    
    # Destination must not be own piece
    if board[nr, nc] != player:
        moves.append((r, c, nr, nc))
    
    return moves

def count_connected_groups(board, player):
    """Count connected groups of pieces using 8-directional connectivity."""
    visited = set()
    groups = 0
    
    for r in range(8):
        for c in range(8):
            if board[r, c] == player and (r, c) not in visited:
                groups += 1
                queue = deque([(r, c)])
                visited.add((r, c))
                
                while queue:
                    curr_r, curr_c = queue.popleft()
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = curr_r + dr, curr_c + dc
                            if 0 <= nr < 8 and 0 <= nc < 8:
                                if board[nr, nc] == player and (nr, nc) not in visited:
                                    visited.add((nr, nc))
                                    queue.append((nr, nc))
    
    return groups

def evaluate(board, player):
    """Evaluate the board position from the perspective of player."""
    my_groups = count_connected_groups(board, player)
    opp_groups = count_connected_groups(board, -player)
    
    my_pieces = np.sum(board == player)
    opp_pieces = np.sum(board == -player)
    
    # Win/lose conditions
    if my_pieces == 0:
        return -1000000
    if my_groups == 1:
        return 1000000
    if opp_pieces == 0:
        return 1000000
    if opp_groups == 1:
        return -1000000
    
    score = 0
    score -= my_groups * 10000  # Fewer groups is primary
    score += opp_groups * 10000
    score += my_pieces * 50
    score -= opp_pieces * 50
    
    return score

def make_move(board, move):
    """Apply a move to the board and return the new board."""
    new_board = board.copy()
    fr, fc, tr, tc = move
    new_board[tr, tc] = new_board[fr, fc]
    new_board[fr, fc] = 0
    return new_board

def order_moves(board, moves, player):
    """Order moves for better alpha-beta pruning."""
    scored = []
    for move in moves:
        fr, fc, tr, tc = move
        score = 0
        
        # Captures are good
        if board[tr, tc] == -player:
            score += 100
        
        # Prefer moves toward center
        dist_before = abs(fr - 3.5) + abs(fc - 3.5)
        dist_after = abs(tr - 3.5) + abs(tc - 3.5)
        if dist_after < dist_before:
            score += 10
        
        scored.append((score, move))
    
    scored.sort(key=lambda x: -x[0])
    return [m for _, m in scored]

def alpha_beta_search(board, player, moves):
    """Alpha-beta search with iterative deepening."""
    start_time = time.time()
    
    best_move = moves[0]
    ordered_moves = order_moves(board, moves, player)
    
    # Adaptive depth based on branching factor
    if len(moves) < 20:
        max_depth = 5
    elif len(moves) < 50:
        max_depth = 4
    else:
        max_depth = 3
    
    for depth in range(1, max_depth + 1):
        if time.time() - start_time > 0.9:
            break
        
        best_score = -float('inf')
        alpha = -float('inf')
        beta = float('inf')
        
        for move in ordered_moves:
            if time.time() - start_time > 0.9:
                break
            
            new_board = make_move(board, move)
            score = -alpha_beta(new_board, -player, depth - 1, -beta, -alpha)
            
            if score > best_score:
                best_score = score
                best_move = move
            
            alpha = max(alpha, score)
    
    return best_move

def alpha_beta(board, player, depth, alpha, beta):
    """Alpha-beta recursive helper."""
    if depth == 0:
        return evaluate(board, player)
    
    moves = generate_all_moves(board, player)
    
    if not moves:
        return evaluate(board, player)
    
    best_score = -float('inf')
    
    for move in moves:
        new_board = make_move(board, move)
        score = -alpha_beta(new_board, -player, depth - 1, -beta, -alpha)
        
        if score > best_score:
            best_score = score
        
        alpha = max(alpha, score)
        
        if alpha >= beta:
            break
    
    return best_score
