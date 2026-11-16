
import numpy as np
from collections import deque

def policy(board):
    # Get current player's pieces (1) and opponent's pieces (-1)
    current_player = 1
    opponent = -1
    
    # Generate all legal moves
    moves = generate_legal_moves(board, current_player)
    
    if not moves:
        # Shouldn't happen in valid games, but return a dummy move
        return "0,0:0,0"
    
    # Evaluate each move and pick the best
    best_move = moves[0]
    best_score = -float('inf')
    
    for move in moves:
        # Parse move
        from_str, to_str = move.split(':')
        from_row, from_col = map(int, from_str.split(','))
        to_row, to_col = map(int, to_str.split(','))
        
        # Simulate move
        new_board = simulate_move(board, from_row, from_col, to_row, to_col)
        
        # Calculate score for this move
        score = evaluate_board(new_board, current_player)
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move

def generate_legal_moves(board, player):
    moves = []
    n = 8
    directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
    
    for r in range(n):
        for c in range(n):
            if board[r][c] == player:
                # Try each direction
                for dr, dc in directions:
                    # Count total pieces (both players) in this line
                    line_pieces = 0
                    blocked = False
                    # We need to count continuous pieces in this direction until we hit edge or block
                    step = 1
                    while True:
                        nr, nc = r + step * dr, c + step * dc
                        if nr < 0 or nr >= n or nc < 0 or nc >= n:
                            break
                        if board[nr][nc] == player:
                            # Friendly piece: can jump over
                            line_pieces += 1
                            step += 1
                            continue
                        elif board[nr][nc] == -player:
                            # Enemy piece: we can land here (if we jump over no one) but block movement beyond
                            line_pieces += 1
                            # Must move exactly line_pieces squares
                            if step == line_pieces:
                                moves.append(f"{r},{c}:{nr},{nc}")
                            break
                        else:  # empty
                            # Must move exactly line_pieces squares
                            if step == line_pieces:
                                moves.append(f"{r},{c}:{nr},{nc}")
                            # Continue to check further steps (can we jump over later?) 
                            # But we cannot jump over opponent, so if there's an empty beyond, it's only valid if distance equals line_pieces
                            step += 1
                            continue
                    
    return moves

def simulate_move(board, from_row, from_col, to_row, to_col):
    # Create a copy of the board
    new_board = np.array(board)
    # Move piece from source to target
    piece = new_board[from_row, from_col]
    new_board[from_row, from_col] = 0
    new_board[to_row, to_col] = piece
    return new_board

def count_connected_components(board, player):
    """Count connected components for player (8-directional) using BFS"""
    n = 8
    visited = [[False]*n for _ in range(n)]
    components = 0
    
    for r in range(n):
        for c in range(n):
            if board[r][c] == player and not visited[r][c]:
                components += 1
                # BFS
                queue = deque([(r, c)])
                visited[r][c] = True
                while queue:
                    cr, cc = queue.popleft()
                    # 8 directions
                    for dr in [-1,0,1]:
                        for dc in [-1,0,1]:
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = cr + dr, cc + dc
                            if 0 <= nr < n and 0 <= nc < n and board[nr][nc] == player and not visited[nr][nc]:
                                visited[nr][nc] = True
                                queue.append((nr, nc))
    
    return components

def evaluate_board(board, player):
    """Return a score for the board: higher is better for current player"""
    opponent = -player
    
    # Compute connected components for both players
    our_components = count_connected_components(board, player)
    their_components = count_connected_components(board, opponent)
    
    # Scoring: we want our components to be low, theirs to be high
    # Base score: favor reducing our components and increasing theirs
    score = (their_components - our_components) * 5
    
    # Bonus for capturing: if we removed an opponent piece, that's good
    # We don't track previous board, so we look at piece count difference
    # But we can't easily do that without previous state.
    
    # Instead: check if this move captured an opponent piece
    # We can't know without previous state, so let's assume we're evaluating final state
    
    # Count pieces for both
    our_pieces = np.sum(board == player)
    their_pieces = np.sum(board == opponent)
    
    # If they have fewer pieces, we've captured
    # We don't know previous opponent count, so let's just use piece count difference as proxy
    # But we can't trust absolute count because pieces can be added? No, pieces only removed by capture.
    # So fewer opponent pieces = good
    
    # We'll use opponent piece count: lower means we've captured -> bonus
    capture_bonus = 0
    # If opponent has less than original? We don't know original... 
    # Instead, we can assume that reducing opponent pieces is good
    # But without context, let's use relative: a big advantage in piece count is good
    # However, the goal is connectivity, not piece count.
    
    # Let's add center proximity bonus: moving toward center is good for control
    # But this is a secondary heuristic
    
    # For simplicity, let's use the connected components as primary, and add piece count advantage
    score += (their_pieces - our_pieces)  # We want opponent to have fewer pieces than us, so if we have more pieces, it's good
    
    # If we have only one component, we might be winning! Add bonus
    if our_components <= 1:
        score += 100  # Very good!
    
    # If opponent has only one component, we penalize
    if their_components <= 1:
        score -= 50
    
    # If we captured at least one piece (opponent has fewer than initial? we don't know initial...)
    # We'll skip the capture bonus since we don't have memory of the prior state.
    
    return score
