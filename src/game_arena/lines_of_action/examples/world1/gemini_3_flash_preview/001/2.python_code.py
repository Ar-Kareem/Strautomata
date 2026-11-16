
import collections
import time

def get_legal_moves(board, player):
    moves = []
    opponent = -player
    pieces = [(r, c) for r in range(8) for c in range(8) if board[r][c] == player]
    
    directions = [(0, 1), (1, 0), (1, 1), (1, -1), (0, -1), (-1, 0), (-1, -1), (-1, 1)]
    
    for r, c in pieces:
        for dr, dc in directions:
            # Count pieces in line
            count = 0
            # Check both directions along the line
            for step in [1, -1]:
                curr_r, curr_c = r, c
                while 0 <= curr_r < 8 and 0 <= curr_c < 8:
                    if board[curr_r][curr_c] != 0:
                        count += 1
                    curr_r += dr * step
                    curr_c += dc * step
            count -= 1 # Don't double count the piece itself
            
            # Destination
            tr, tc = r + dr * count, c + dc * count
            
            if 0 <= tr < 8 and 0 <= tc < 8:
                # Rule: Can't land on own piece
                if board[tr][tc] == player:
                    continue
                
                # Rule: Can't jump over enemy piece
                blocked = False
                for step in range(1, count):
                    mr, mc = r + dr * step, c + dc * step
                    if board[mr][mc] == opponent:
                        blocked = True
                        break
                
                if not blocked:
                    moves.append(((r, c), (tr, tc)))
    return moves

def count_groups(board, player):
    pieces = [(r, c) for r in range(8) for c in range(8) if board[r][c] == player]
    if not pieces: return 0
    visited = set()
    groups = 0
    for p in pieces:
        if p not in visited:
            groups += 1
            stack = [p]
            visited.add(p)
            while stack:
                curr_r, curr_c = stack.pop()
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        nr, nc = curr_r + dr, curr_c + dc
                        if 0 <= nr < 8 and 0 <= nc < 8 and board[nr][nc] == player and (nr, nc) not in visited:
                            visited.add((nr, nc))
                            stack.append((nr, nc))
    return groups

def evaluate(board, player):
    # Quick check for win/loss
    p_groups = count_groups(board, player)
    o_groups = count_groups(board, -player)
    
    if p_groups == 1: return 10000
    if o_groups == 1: return -10000
    
    # Connection incentive
    score = -50 * p_groups + 50 * o_groups
    
    # Centralization / Cohesion
    p_pieces = [(r, c) for r in range(8) for c in range(8) if board[r][c] == player]
    if p_pieces:
        mean_r = sum(r for r, c in p_pieces) / len(p_pieces)
        mean_c = sum(c for r, c in p_pieces) / len(p_pieces)
        dist = sum(abs(r - mean_r) + abs(c - mean_c) for r, c in p_pieces)
        score -= dist * 2
        
    return score

def minimax(board, depth, alpha, beta, player, start_time):
    if depth == 0 or time.time() - start_time > 0.8:
        return evaluate(board, 1), None
    
    moves = get_legal_moves(board, player)
    if not moves: # Check if game over by blocking or no pieces
        return evaluate(board, 1), None
    
    best_move = None
    if player == 1:
        max_eval = -float('inf')
        for move in moves:
            (fr, fc), (tr, tc) = move
            old_val = board[tr][tc]
            board[tr][tc] = 1
            board[fr][fc] = 0
            eval_val, _ = minimax(board, depth - 1, alpha, beta, -1, start_time)
            board[fr][fc] = 1
            board[tr][tc] = old_val
            if eval_val > max_eval:
                max_eval = eval_val
                best_move = move
            alpha = max(alpha, eval_val)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for move in moves:
            (fr, fc), (tr, tc) = move
            old_val = board[tr][tc]
            board[tr][tc] = -1
            board[fr][fc] = 0
            eval_val, _ = minimax(board, depth - 1, alpha, beta, 1, start_time)
            board[fr][fc] = -1
            board[tr][tc] = old_val
            if eval_val < min_eval:
                min_eval = eval_val
                best_move = move
            beta = min(beta, eval_val)
            if beta <= alpha:
                break
        return min_eval, best_move

def policy(board) -> str:
    # 1 is us, -1 is opponent
    # Board is 8x8 ints
    start_time = time.time()
    _, best_move = minimax(board, 2, -float('inf'), float('inf'), 1, start_time)
    
    if not best_move:
        # Fallback to first legal move
        moves = get_legal_moves(board, 1)
        if not moves: return ""
        best_move = moves[0]
        
    (fr, fc), (tr, tc) = best_move
    return f"{fr},{fc}:{tr},{tc}"

