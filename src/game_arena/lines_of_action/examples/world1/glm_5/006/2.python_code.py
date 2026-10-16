
import numpy as np
import time
import collections

# Directions for movement and connectivity (8 directions)
DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]

def get_moves(board, player):
    """Generates all legal moves for the given player."""
    rows, cols = board.shape
    moves = []
    
    # Find all piece positions for the player
    pieces_r, pieces_c = np.where(board == player)
    
    for r, c in zip(pieces_r, pieces_c):
        for dr, dc in DIRS:
            # Count pieces in the line of movement
            count = 0
            
            # Walk positive direction
            nr, nc = r, c
            while 0 <= nr < rows and 0 <= nc < cols:
                if board[nr, nc] != 0:
                    count += 1
                nr += dr
                nc += dc
            
            # Walk negative direction (excluding current spot)
            nr, nc = r - dr, c - dc
            while 0 <= nr < rows and 0 <= nc < cols:
                if board[nr, nc] != 0:
                    count += 1
                nr -= dr
                nc -= dc
            
            if count == 0:
                continue
                
            # Determine target position
            tr, tc = r + count * dr, c + count * dc
            
            # Check bounds
            if not (0 <= tr < rows and 0 <= tc < cols):
                continue
            
            # Check path for enemy pieces (blocking)
            blocked = False
            for step in range(1, count):
                pr, pc = r + step * dr, c + step * dc
                if board[pr, pc] == -player:
                    blocked = True
                    break
            if blocked:
                continue
            
            # Check landing spot (cannot land on own piece)
            if board[tr, tc] == player:
                continue
            
            # Capture heuristic for ordering: prioritize captures
            move = ((r, c), (tr, tc))
            # Append with a priority flag (higher is better)
            # Captures (landing on enemy) get priority
            priority = 1 if board[tr, tc] == -player else 0
            moves.append((priority, move))
            
    # Sort moves by priority (descending)
    moves.sort(key=lambda x: x[0], reverse=True)
    return [m[1] for m in moves]

def make_move(board, move):
    """Applies a move to the board and returns the new board state."""
    new_board = board.copy()
    (r1, c1), (r2, c2) = move
    piece = new_board[r1, c1]
    new_board[r1, c1] = 0
    new_board[r2, c2] = piece
    return new_board

def count_components(board, player):
    """Counts the number of connected components for a player."""
    rows, cols = board.shape
    visited = np.zeros((rows, cols), dtype=bool)
    count = 0
    
    pieces_r, pieces_c = np.where(board == player)
    
    for r, c in zip(pieces_r, pieces_c):
        if not visited[r, c]:
            count += 1
            # BFS
            queue = collections.deque([(r, c)])
            visited[r, c] = True
            while queue:
                curr_r, curr_c = queue.popleft()
                for dr, dc in DIRS:
                    nr, nc = curr_r + dr, curr_c + dc
                    if 0 <= nr < rows and 0 <= nc < cols:
                        if board[nr, nc] == player and not visited[nr, nc]:
                            visited[nr, nc] = True
                            queue.append((nr, nc))
    return count

def evaluate(board):
    """Evaluates the board state for Player 1 (Max)."""
    # Check win/loss conditions
    p1_comp = count_components(board, 1)
    p2_comp = count_components(board, -1)
    
    # If I have 1 component, I win
    if p1_comp == 1:
        return 100000
    # If opponent has 1 component, I lose
    if p2_comp == 1:
        return -100000
        
    # Heuristic scoring
    # Minimize my components, maximize opponent components (fragment them)
    # Weight components very highly
    score = (p2_comp - p1_comp) * 1000
    
    # Material advantage
    my_pieces = np.sum(board == 1)
    opp_pieces = np.sum(board == -1)
    score += (my_pieces - opp_pieces) * 10
    
    return score

def minimax(board, depth, alpha, beta, maximizing_player, start_time, time_limit):
    """Minimax with Alpha-Beta pruning."""
    if time.time() - start_time > time_limit:
        return None, 0

    player = 1 if maximizing_player else -1
    moves = get_moves(board, player)
    
    if depth == 0 or not moves:
        return None, evaluate(board)
    
    best_move = moves[0] if moves else None
    
    if maximizing_player:
        max_eval = -float('inf')
        for move in moves:
            new_board = make_move(board, move)
            _, eval_val = minimax(new_board, depth - 1, alpha, beta, False, start_time, time_limit)
            
            if time.time() - start_time > time_limit:
                return None, max_eval
                
            if eval_val > max_eval:
                max_eval = eval_val
                best_move = move
            alpha = max(alpha, eval_val)
            if beta <= alpha:
                break
        return best_move, max_eval
    else:
        min_eval = float('inf')
        for move in moves:
            new_board = make_move(board, move)
            _, eval_val = minimax(new_board, depth - 1, alpha, beta, True, start_time, time_limit)
            
            if time.time() - start_time > time_limit:
                return None, min_eval
                
            if eval_val < min_eval:
                min_eval = eval_val
                best_move = move
            beta = min(beta, eval_val)
            if beta <= alpha:
                break
        return best_move, min_eval

def policy(board):
    start_time = time.time()
    time_limit = 0.95 # seconds
    
    # Ensure board is numpy array
    board = np.array(board, dtype=int)
    
    best_move = None
    
    # Iterative Deepening
    for depth in range(1, 8):
        move, score = minimax(board, depth, -float('inf'), float('inf'), True, start_time, time_limit)
        
        if move is not None:
            best_move = move
        
        # If we found a win, stop searching
        if score >= 100000:
            break
            
        # Check time
        if time.time() - start_time > time_limit * 0.7:
            break
            
    if best_move is None:
        # Fallback: pick first valid move found
        moves = get_moves(board, 1)
        if moves:
            best_move = moves[0]
        else:
            # No legal moves? Should not happen in normal play
            return "0,0:0,0"

    return f"{best_move[0][0]},{best_move[0][1]}:{best_move[1][0]},{best_move[1][1]}"
