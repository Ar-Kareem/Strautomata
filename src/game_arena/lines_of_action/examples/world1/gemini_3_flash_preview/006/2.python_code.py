
import numpy as np
import time

def policy(board) -> str:
    start_time = time.time()
    
    def get_pieces(b, player):
        return [(r, c) for r in range(8) for c in range(8) if b[r][c] == player]

    def is_in_bounds(r, c):
        return 0 <= r < 8 and 0 <= c < 8

    def get_legal_moves(b, player):
        moves = []
        my_pieces = get_pieces(b, player)
        opponent = -player
        
        directions = [(0, 1), (1, 0), (1, 1), (1, -1), (0, -1), (-1, 0), (-1, -1), (-1, 1)]
        
        for r, c in my_pieces:
            for dr, dc in directions:
                # Count pieces in line
                count = 0
                # Forward
                curr_r, curr_c = r, c
                while is_in_bounds(curr_r, curr_c):
                    if b[curr_r][curr_c] != 0: count += 1
                    curr_r += dr
                    curr_c += dc
                # Backward
                curr_r, curr_c = r - dr, c - dc
                while is_in_bounds(curr_r, curr_c):
                    if b[curr_r][curr_c] != 0: count += 1
                    curr_r -= dr
                    curr_c -= dc
                
                tr, tc = r + dr * count, c + dc * count
                if is_in_bounds(tr, tc) and b[tr][tc] != player:
                    # Check for enemy pieces in between
                    blocked = False
                    for step in range(1, count):
                        ir, ic = r + dr * step, c + dc * step
                        if b[ir][ic] == opponent:
                            blocked = True
                            break
                    if not blocked:
                        moves.append(((r, c), (tr, tc)))
        return moves

    def get_score(b, player):
        mine = get_pieces(b, player)
        if not mine: return -10000
        
        # Center of mass
        mr = sum(p[0] for p in mine) / len(mine)
        mc = sum(p[1] for p in mine) / len(mine)
        
        # Square distance mean
        dist_sq = sum((p[0]-mr)**2 + (p[1]-mc)**2 for p in mine)
        
        # Connectivity check (BFS)
        connected_count = 0
        if mine:
            visited = {mine[0]}
            q = [mine[0]]
            while q:
                curr = q.pop(0)
                connected_count += 1
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0: continue
                        neighbor = (curr[0]+dr, curr[1]+dc)
                        if neighbor in mine and neighbor not in visited:
                            visited.add(neighbor)
                            q.append(neighbor)
        
        if connected_count == len(mine): 
            return 10000 
            
        score = -dist_sq * 10
        score += connected_count * 50
        score -= len(mine) * 5 # Fewer pieces is actually harder to connect, but LOA rewards concentration
        
        return score

    def minimax(b, depth, alpha, beta, maximizing_player):
        if depth == 0:
            return get_score(b, 1) - get_score(b, -1)
        
        player = 1 if maximizing_player else -1
        moves = get_legal_moves(b, player)
        if not moves:
            return get_score(b, 1) - get_score(b, -1)

        if maximizing_player:
            max_eval = -float('inf')
            for (fr, fc), (tr, tc) in moves:
                temp_val = b[tr][tc]
                b[tr][tc], b[fr][fc] = 1, 0
                eval = minimax(b, depth - 1, alpha, beta, False)
                b[fr][fc], b[tr][tc] = 1, temp_val
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha: break
            return max_eval
        else:
            min_eval = float('inf')
            for (fr, fc), (tr, tc) in moves:
                temp_val = b[tr][tc]
                b[tr][tc], b[fr][fc] = -1, 0
                eval = minimax(b, depth - 1, alpha, beta, True)
                b[fr][fc], b[tr][tc] = -1, temp_val
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha: break
            return min_eval

    best_move = None
    best_val = -float('inf')
    legal_moves = get_legal_moves(board, 1)
    
    if not legal_moves:
        return ""

    # Depth 2 search
    for (fr, fc), (tr, tc) in legal_moves:
        temp_val = board[tr][tc]
        board[tr][tc], board[fr][fc] = 1, 0
        move_val = minimax(board, 1, -float('inf'), float('inf'), False)
        board[fr][fc], board[tr][tc] = 1, temp_val
        
        if move_val > best_val:
            best_val = move_val
            best_move = f"{fr},{fc}:{tr},{tc}"

    return best_move if best_move else f"{legal_moves[0][0][0]},{legal_moves[0][0][1]}:{legal_moves[0][1][0]},{legal_moves[0][1][1]}"
