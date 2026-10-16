
import sys
from collections import deque

def policy(board):
    """
    Main entry point. Returns a move string for the given board state.
    """
    my_player = 1
    moves = get_legal_moves(board, my_player)
    
    if not moves:
        return "" 

    # Check for immediate wins
    for move in moves:
        new_board = apply_move(board, move)
        if count_components(new_board, my_player) == 1:
            return move_to_str(move)

    # Iterative Deepening or fixed depth. 
    # Depth 3 is chosen to stay safely within 1 second for Python.
    best_move = moves[0]
    best_score = -float('inf')
    
    # Order moves to improve alpha-beta pruning
    moves.sort(key=lambda m: score_move_heuristic(board, m, my_player), reverse=True)
    
    for move in moves:
        new_board = apply_move(board, move)
        # Negamax formulation
        score = -negamax(new_board, 3, -float('inf'), float('inf'), -1)
        if score > best_score:
            best_score = score
            best_move = move
            
    return move_to_str(best_move)

def move_to_str(move):
    r1, c1, r2, c2 = move
    return f"{r1},{c1}:{r2},{c2}"

def score_move_heuristic(board, move, player):
    # Prioritize captures for move ordering
    r1, c1, r2, c2 = move
    score = 0
    if board[r2][c2] == -player:
        score += 10
    # Prioritize centerward moves slightly
    center_dist_prev = abs(r1 - 3.5) + abs(c1 - 3.5)
    center_dist_new = abs(r2 - 3.5) + abs(c2 - 3.5)
    score += (center_dist_prev - center_dist_new) * 0.5
    return score

def negamax(board, depth, alpha, beta, player):
    if depth == 0:
        return evaluate(board, player)
    
    moves = get_legal_moves(board, player)
    
    if not moves:
        # No legal moves means loss in tournament rules usually, or pass.
        # LOA rules typically allow pass if no moves, but evaluation 
        # of a dead state is just heuristic.
        return evaluate(board, player)

    # Check for win
    for move in moves:
        new_board = apply_move(board, move)
        if count_components(new_board, player) == 1:
            return 10000 + depth # Prefer faster wins

    moves.sort(key=lambda m: score_move_heuristic(board, m, player), reverse=True)
    
    max_eval = -float('inf')
    for move in moves:
        new_board = apply_move(board, move)
        # Recursive call with flipped player and negated values
        eval_val = -negamax(new_board, depth - 1, -beta, -alpha, -player)
        
        if eval_val > max_eval:
            max_eval = eval_val
            
        alpha = max(alpha, eval_val)
        if alpha >= beta:
            break
            
    return max_eval

def evaluate(board, player):
    # 1. Connectivity (Primary)
    my_comps = count_components(board, player)
    opp_comps = count_components(board, -player)
    
    # Lower components for me is good, higher for opponent is good.
    # We want to maximize (opp_comps - my_comps)
    # Since negamax maximizes for current player:
    score = (opp_comps - my_comps) * 100
    
    # 2. Piece Count (Captures)
    my_pieces = 0
    opp_pieces = 0
    for r in range(8):
        for c in range(8):
            if board[r][c] == player:
                my_pieces += 1
            elif board[r][c] == -player:
                opp_pieces += 1
    
    # Having more pieces is generally good
    score += (my_pieces - opp_pieces) * 10
    
    # 3. Centralization
    # Pieces closer to center are easier to connect
    center_score = 0
    for r in range(8):
        for c in range(8):
            if board[r][c] == player:
                dist = abs(r - 3.5) + abs(c - 3.5)
                center_score -= dist # Closer is better (lower dist)
    
    score += center_score * 0.5
    
    return score

def get_legal_moves(board, player):
    moves = []
    for r in range(8):
        for c in range(8):
            if board[r][c] == player:
                moves.extend(get_piece_moves(board, r, c, player))
    return moves

def get_piece_moves(board, r, c, player):
    piece_moves = []
    # Directions: N, S, W, E, NW, NE, SW, SE
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1), 
                  (-1, -1), (-1, 1), (1, -1), (1, 1)]
    
    for dr, dc in directions:
        # Calculate number of pieces in the line of action
        line_count = count_line_pieces(board, r, c, dr, dc)
        dist = line_count
        
        tr, tc = r + dr * dist, c + dc * dist
        
        if 0 <= tr < 8 and 0 <= tc < 8:
            # Check path validity
            # Rule: Cannot jump over enemy pieces
            # Rule: Cannot land on friendly piece
            
            # Check path obstruction
            path_clear = True
            # Check intermediate squares (exclusive of start, inclusive of end? No, exclusive of end)
            # A piece jumps 'dist' squares.
            # The squares between (r,c) and (tr,tc) must be checked for enemy pieces.
            
            curr_r, curr_c = r + dr, c + dc
            # We iterate dist-1 times for the path, the landing square is checked separately
            for _ in range(dist - 1):
                # If there is an enemy piece in the path, we cannot jump over it
                if board[curr_r][curr_c] == -player:
                    path_clear = False
                    break
                curr_r += dr
                curr_c += dc
            
            if path_clear:
                # Check landing square
                if board[tr][tc] != player:
                    piece_moves.append((r, c, tr, tc))
                    
    return piece_moves

def count_line_pieces(board, r, c, dr, dc):
    count = 0
    # The line passes through (r, c) with direction (dr, dc).
    # We must count all pieces on this line.
    
    if dr == 0: # Horizontal
        for i in range(8):
            if board[r][i] != 0:
                count += 1
    elif dc == 0: # Vertical
        for i in range(8):
            if board[i][c] != 0:
                count += 1
    else: # Diagonal
        # Find start of diagonal to count whole line
        cr, cc = r, c
        # Trace back to edge
        while 0 <= cr - dr < 8 and 0 <= cc - dc < 8:
            cr -= dr
            cc -= dc
        # Trace forward
        while 0 <= cr < 8 and 0 <= cc < 8:
            if board[cr][cc] != 0:
                count += 1
            cr += dr
            cc += dc
            
    return count

def apply_move(board, move):
    r1, c1, r2, c2 = move
    new_board = [row[:] for row in board] # Deep copy
    piece = new_board[r1][c1]
    new_board[r1][c1] = 0
    new_board[r2][c2] = piece
    return new_board

def count_components(board, player):
    # BFS to count connected components
    visited = [[False for _ in range(8)] for _ in range(8)]
    components = 0
    
    for r in range(8):
        for c in range(8):
            if board[r][c] == player and not visited[r][c]:
                components += 1
                # BFS
                q = deque([(r, c)])
                visited[r][c] = True
                while q:
                    cr, cc = q.popleft()
                    # 8 neighbors
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0: continue
                            nr, nc = cr + dr, cc + dc
                            if 0 <= nr < 8 and 0 <= nc < 8:
                                if board[nr][nc] == player and not visited[nr][nc]:
                                    visited[nr][nc] = True
                                    q.append((nr, nc))
    return components
