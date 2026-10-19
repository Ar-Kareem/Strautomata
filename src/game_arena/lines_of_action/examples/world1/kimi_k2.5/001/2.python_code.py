
import numpy as np
from collections import deque

# 8 directions: row_delta, col_delta
DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

def get_line_count(board, r, c, dr, dc):
    """Count total pieces in the line of movement including the piece at (r,c)"""
    if dr == 0:  # Horizontal
        return np.sum(board[r, :] != 0)
    elif dc == 0:  # Vertical
        return np.sum(board[:, c] != 0)
    elif dr == dc:  # Main diagonal (r-c constant)
        return np.sum(np.diagonal(board, offset=c - r) != 0)
    else:  # Anti-diagonal (r+c constant)
        s = r + c
        count = 0
        start_i = max(0, s - 7)
        end_i = min(7, s)
        for i in range(start_i, end_i + 1):
            if board[i, s - i] != 0:
                count += 1
        return count

def generate_moves(board, player):
    """Generate all legal moves for player (1 or -1)"""
    moves = []
    pieces = np.argwhere(board == player)
    
    for r, c in pieces:
        for dr, dc in DIRECTIONS:
            step_count = get_line_count(board, r, c, dr, dc)
            if step_count == 0:
                continue
            
            dest_r = r + dr * step_count
            dest_c = c + dc * step_count
            
            # Check bounds
            if not (0 <= dest_r < 8 and 0 <= dest_c < 8):
                continue
            
            # Cannot land on own piece
            if board[dest_r, dest_c] == player:
                continue
            
            # Check path is clear of enemy pieces (can jump over friendly)
            blocked = False
            for step in range(1, step_count):
                rr = r + dr * step
                cc = c + dc * step
                if board[rr, cc] == -player:  # Enemy piece blocks
                    blocked = True
                    break
            
            if not blocked:
                moves.append((r, c, dest_r, dest_c))
    
    return moves

def apply_move(board, move):
    """Return new board after applying move (r1, c1, r2, c2)"""
    r1, c1, r2, c2 = move
    new_board = board.copy()
    new_board[r1, c1] = 0
    new_board[r2, c2] = 1  # Current player's piece
    return new_board

def check_connected(board, player):
    """Check if all pieces of player form a single connected component (8-connectivity)"""
    pieces = list(zip(*np.where(board == player)))
    n = len(pieces)
    if n <= 1:
        return True
    
    # BFS from first piece
    visited = set([pieces[0]])
    queue = deque([pieces[0]])
    count = 1
    
    while queue:
        r, c = queue.popleft()
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    if board[nr, nc] == player and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        queue.append((nr, nc))
                        count += 1
    
    return count == n

def count_components(board, player):
    """Count number of connected components for player"""
    pieces = set(zip(*np.where(board == player)))
    if not pieces:
        return 0
    components = 0
    
    while pieces:
        start = pieces.pop()
        components += 1
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if (nr, nc) in pieces:
                        pieces.remove((nr, nc))
                        queue.append((nr, nc))
    return components

def evaluate(board):
    """Static evaluation from perspective of player 1"""
    # Terminal checks
    if check_connected(board, 1):
        return 10000
    if check_connected(board, -1):
        return -10000
    
    score = 0
    
    # Fewer components is better for me
    my_comp = count_components(board, 1)
    score -= my_comp * 200
    
    # More components is better for opponent (harder for them to connect)
    opp_comp = count_components(board, -1)
    score += opp_comp * 100
    
    # Mobility
    my_moves = len(generate_moves(board, 1))
    opp_moves = len(generate_moves(board, -1))
    score += my_moves * 2
    score -= opp_moves * 1
    
    return score

def negamax(board, depth, alpha, beta):
    """Negamax search with alpha-beta pruning"""
    if depth == 0:
        return evaluate(board)
    
    moves = generate_moves(board, 1)
    if not moves:
        return -5000  # No moves available - bad position
    
    for move in moves:
        new_board = apply_move(board, move)
        # Negate board to switch perspective
        score = -negamax(-new_board, depth - 1, -beta, -alpha)
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
    
    return alpha

def policy(board):
    board = np.array(board)
    moves = generate_moves(board, 1)
    
    if not moves:
        return "0,0:0,0"  # Should not happen in valid game state
    
    # Check for immediate win
    for move in moves:
        new_board = apply_move(board, move)
        if check_connected(new_board, 1):
            r1, c1, r2, c2 = move
            return f"{r1},{c1}:{r2},{c2}"
    
    # Search depth 2 (1 ply opponent response)
    best_move = None
    best_score = -float('inf')
    
    for move in moves:
        new_board = apply_move(board, move)
        # Opponent's turn, search 1 ply deep
        score = -negamax(-new_board, 1, -float('inf'), float('inf'))
        if score > best_score:
            best_score = score
            best_move = move
    
    if best_move is None:
        best_move = moves[0]
    
    r1, c1, r2, c2 = best_move
    return f"{r1},{c1}:{r2},{c2}"
