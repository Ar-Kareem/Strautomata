
import numpy as np
import time
from collections import deque

def policy(board) -> str:
    """
    Lines of Action policy using minimax with alpha-beta pruning.
    """
    board_np = np.array(board, dtype=int)
    start_time = time.time()
    max_time = 0.9  # Leave some margin
    
    # Find all legal moves for the current player (1)
    moves = get_legal_moves(board_np, 1)
    
    if not moves:
        # No legal moves, return a dummy move (shouldn't happen in normal play)
        return "0,0:0,0"
    
    # If only one move available, return it immediately
    if len(moves) == 1:
        fr, fc, tr, tc = moves[0]
        return f"{fr},{fc}:{tr},{tc}"
    
    # Iterative deepening search
    best_move = moves[0]
    depth = 1
    max_depth = 4
    
    while depth <= max_depth:
        if time.time() - start_time > max_time * 0.5:
            break
        
        current_best = None
        alpha = float('-inf')
        beta = float('inf')
        
        # Sort moves for better pruning (captures first, then central moves)
        sorted_moves = order_moves(board_np, moves, 1)
        
        for move in sorted_moves:
            new_board = apply_move(board_np, move)
            value = minimax(new_board, depth - 1, False, alpha, beta, start_time, max_time)
            
            if value > alpha:
                alpha = value
                current_best = move
            
            if time.time() - start_time > max_time * 0.8:
                break
        
        if current_best is not None:
            best_move = current_best
        
        depth += 1
    
    fr, fc, tr, tc = best_move
    return f"{fr},{fc}:{tr},{tc}"


def get_legal_moves(board, player):
    """Get all legal moves for the given player."""
    moves = []
    rows, cols = board.shape
    pieces = np.argwhere(board == player)
    
    for r, c in pieces:
        # Check all 8 directions
        for dr, dc in [(0,1), (1,0), (0,-1), (-1,0), (1,1), (-1,-1), (1,-1), (-1,1)]:
            # Count pieces in this line
            count = count_in_line(board, r, c, dr, dc)
            
            # Calculate target position
            tr = r + dr * count
            tc = c + dc * count
            
            # Check if target is on board
            if 0 <= tr < rows and 0 <= tc < cols:
                # Check if path is clear (no enemy pieces in between)
                if is_path_clear(board, r, c, tr, tc, dr, dc, player):
                    # Check if target is empty or has enemy piece
                    if board[tr, tc] != player:
                        moves.append((r, c, tr, tc))
    
    return moves


def count_in_line(board, r, c, dr, dc):
    """Count pieces (both players) in the line starting from (r,c) going in direction (dr,dc)."""
    count = 0
    rows, cols = board.shape
    cr, cc = r, c
    
    # Count in positive direction
    while 0 <= cr < rows and 0 <= cc < cols:
        if board[cr, cc] != 0:
            count += 1
        cr += dr
        cc += dc
    
    # Count in negative direction (excluding the starting piece)
    cr, cc = r - dr, c - dc
    while 0 <= cr < rows and 0 <= cc < cols:
        if board[cr, cc] != 0:
            count += 1
        cr -= dr
        cc -= dc
    
    return count


def is_path_clear(board, r, c, tr, tc, dr, dc, player):
    """Check if the path from (r,c) to (tr,tc) doesn't contain enemy pieces."""
    cr, cc = r + dr, c + dc
    while cr != tr or cc != tc:
        if board[cr, cc] == -player:
            return False
        cr += dr
        cc += dc
    return True


def apply_move(board, move):
    """Apply a move and return the new board state."""
    fr, fc, tr, tc = move
    new_board = board.copy()
    new_board[tr, tc] = new_board[fr, fc]
    new_board[fr, fc] = 0
    return new_board


def order_moves(board, moves, player):
    """Order moves for better alpha-beta pruning (captures first)."""
    scored_moves = []
    for move in moves:
        fr, fc, tr, tc = move
        # Score captures higher
        score = 0
        if board[tr, tc] == -player:
            score = 10
        # Score center moves higher
        score += 3 - (abs(tr - 3.5) + abs(tc - 3.5)) / 7.0
        scored_moves.append((score, move))
    
    scored_moves.sort(reverse=True)
    return [move for _, move in scored_moves]


def minimax(board, depth, is_maximizing, alpha, beta, start_time, max_time):
    """Minimax with alpha-beta pruning."""
    if time.time() - start_time > max_time:
        return evaluate(board)
    
    if depth == 0:
        return evaluate(board)
    
    if is_maximizing:
        value = float('-inf')
        moves = get_legal_moves(board, 1)
        if not moves:
            return evaluate(board)
        
        moves = order_moves(board, moves, 1)
        for move in moves:
            new_board = apply_move(board, move)
            value = max(value, minimax(new_board, depth-1, False, alpha, beta, start_time, max_time))
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value
    else:
        value = float('inf')
        moves = get_legal_moves(board, -1)
        if not moves:
            return evaluate(board)
        
        moves = order_moves(board, moves, -1)
        for move in moves:
            new_board = apply_move(board, move)
            value = min(value, minimax(new_board, depth-1, True, alpha, beta, start_time, max_time))
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value


def evaluate(board):
    """Evaluate the board from the perspective of player 1."""
    rows, cols = board.shape
    
    # Check for winning condition (all pieces connected)
    my_pieces = np.argwhere(board == 1)
    opp_pieces = np.argwhere(board == -1)
    
    # If a player has won, return extreme value
    if is_connected(board, 1):
        return 1000
    if is_connected(board, -1):
        return -1000
    
    # Count pieces
    my_count = len(my_pieces)
    opp_count = len(opp_pieces)
    
    if my_count == 0:
        return -1000
    if opp_count == 0:
        return 1000
    
    score = 0
    
    # 1. Connectivity score - measure largest connected component
    my_connectivity = largest_connected_component(board, 1) / max(my_count, 1)
    opp_connectivity = largest_connected_component(board, -1) / max(opp_count, 1)
    score += (my_connectivity - opp_connectivity) * 50
    
    # 2. Centrality score
    my_center_dist = np.mean(np.sum((my_pieces - 3.5)**2, axis=1)) if my_count > 0 else 100
    opp_center_dist = np.mean(np.sum((opp_pieces - 3.5)**2, axis=1)) if opp_count > 0 else 100
    score -= (my_center_dist - opp_center_dist) * 0.1
    
    # 3. Piece advantage
    score += (my_count - opp_count) * 5
    
    # 4. Mobility (simplified)
    my_mobility = len(get_legal_moves(board, 1))
    score += my_mobility * 0.5
    
    return score


def is_connected(board, player):
    """Check if all pieces of the given player are connected (8-directional)."""
    pieces = np.argwhere(board == player)
    if len(pieces) <= 1:
        return len(pieces) == 1
    
    # BFS from first piece
    visited = set()
    queue = deque()
    start = tuple(pieces[0])
    queue.append(start)
    visited.add(start)
    
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
    
    return len(visited) == len(pieces)


def largest_connected_component(board, player):
    """Return the size of the largest connected component for the given player."""
    pieces = np.argwhere(board == player)
    if len(pieces) == 0:
        return 0
    if len(pieces) == 1:
        return 1
    
    all_positions = set(tuple(p) for p in pieces)
    visited = set()
    max_component = 0
    
    for piece in pieces:
        pos = tuple(piece)
        if pos not in visited:
            component_size = 0
            queue = deque([pos])
            visited.add(pos)
            
            while queue:
                r, c = queue.popleft()
                component_size += 1
                
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        neighbor = (nr, nc)
                        if neighbor in all_positions and neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)
            
            max_component = max(max_component, component_size)
    
    return max_component

