
import numpy as np
from collections import deque
import time

def policy(board) -> str:
    board = np.array(board)
    start_time = time.time()
    time_limit = 0.85
    
    DIRS = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
    
    def get_pieces(bd, player):
        return list(zip(*np.where(bd == player)))
    
    def count_components(bd, player):
        pieces = get_pieces(bd, player)
        if not pieces:
            return 0, 0
        piece_set = set(pieces)
        visited = set()
        components = 0
        max_size = 0
        for p in pieces:
            if p not in visited:
                components += 1
                q = deque([p])
                visited.add(p)
                size = 0
                while q:
                    r, c = q.popleft()
                    size += 1
                    for dr, dc in DIRS:
                        nr, nc = r+dr, c+dc
                        if (nr, nc) in piece_set and (nr, nc) not in visited:
                            visited.add((nr, nc))
                            q.append((nr, nc))
                max_size = max(max_size, size)
        return components, max_size
    
    def is_connected(bd, player):
        pieces = get_pieces(bd, player)
        if len(pieces) <= 1:
            return True
        piece_set = set(pieces)
        visited = set()
        q = deque([pieces[0]])
        visited.add(pieces[0])
        while q:
            r, c = q.popleft()
            for dr, dc in DIRS:
                nr, nc = r+dr, c+dc
                if (nr, nc) in piece_set and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    q.append((nr, nc))
        return len(visited) == len(pieces)
    
    def get_legal_moves(bd, player):
        moves = []
        pieces = get_pieces(bd, player)
        opp = -player
        for r, c in pieces:
            for dr, dc in DIRS:
                # Count pieces in this line
                if dr == 0 and dc == 0:
                    continue
                # Count all pieces along the full line through (r,c)
                count = 0
                # Count in direction (dr, dc)
                nr, nc = r, c
                while 0 <= nr < 8 and 0 <= nc < 8:
                    if bd[nr][nc] != 0:
                        count += 1
                    nr += dr
                    nc += dc
                # Count in direction (-dr, -dc), excluding (r,c) itself
                nr, nc = r - dr, c - dc
                while 0 <= nr < 8 and 0 <= nc < 8:
                    if bd[nr][nc] != 0:
                        count += 1
                    nr -= dr
                    nc -= dc
                
                dist = count
                tr, tc = r + dr * dist, c + dc * dist
                if not (0 <= tr < 8 and 0 <= tc < 8):
                    continue
                # Check path: can't jump over opponent pieces
                blocked = False
                for step in range(1, dist):
                    mr, mc = r + dr * step, c + dc * step
                    if bd[mr][mc] == opp:
                        blocked = True
                        break
                if blocked:
                    continue
                # Can't land on own piece
                if bd[tr][tc] == player:
                    continue
                moves.append((r, c, tr, tc))
        return moves
    
    def evaluate(bd, player):
        opp = -player
        my_pieces = get_pieces(bd, player)
        opp_pieces = get_pieces(bd, opp)
        
        if len(my_pieces) <= 1:
            return 100000
        if len(opp_pieces) <= 1:
            return -100000
        
        my_comps, my_max = count_components(bd, player)
        opp_comps, opp_max = count_components(bd, opp)
        
        if my_comps == 1:
            return 100000
        if opp_comps == 1:
            return -100000
        
        # Center of mass distance
        my_cr = sum(r for r, c in my_pieces) / len(my_pieces)
        my_cc = sum(c for r, c in my_pieces) / len(my_pieces)
        my_dist = sum(abs(r - my_cr) + abs(c - my_cc) for r, c in my_pieces)
        
        opp_cr = sum(r for r, c in opp_pieces) / len(opp_pieces)
        opp_cc = sum(c for r, c in opp_pieces) / len(opp_pieces)
        opp_dist = sum(abs(r - opp_cr) + abs(c - opp_cc) for r, c in opp_pieces)
        
        # Adjacency count
        my_adj = 0
        my_set = set(my_pieces)
        for r, c in my_pieces:
            for dr, dc in DIRS:
                if (r+dr, c+dc) in my_set:
                    my_adj += 1
        
        opp_adj = 0
        opp_set = set(opp_pieces)
        for r, c in opp_pieces:
            for dr, dc in DIRS:
                if (r+dr, c+dc) in opp_set:
                    opp_adj += 1
        
        score = 0
        score += (opp_comps - my_comps) * 300
        score += (my_max - opp_max) * 100
        score += (opp_dist - my_dist) * 15
        score += (my_adj - opp_adj) * 40
        # Bonus for fewer pieces being in separate components
        score += (len(my_pieces) - my_max) * (-50)
        score += (len(opp_pieces) - opp_max) * 50
        
        return score
    
    def make_move(bd, r, c, tr, tc, player):
        new_bd = bd.copy()
        new_bd[r][c] = 0
        new_bd[tr][tc] = player
        return new_bd
    
    def alphabeta(bd, player, depth, alpha, beta, maximizing):
        if time.time() - start_time > time_limit:
            return evaluate(bd, 1), None
        
        current = 1 if maximizing else -1
        moves = get_legal_moves(bd, current)
        
        if not moves:
            return evaluate(bd, 1), None
        
        if depth == 0:
            return evaluate(bd, 1), None
        
        # Move ordering
        def move_score(m):
            r, c, tr, tc = m
            s = 0
            if bd[tr][tc] == -current:  # capture
                s += 1000
            # Prefer moves toward center of mass of own pieces
            pieces = get_pieces(bd, current)
            cr = sum(p[0] for p in pieces) / len(pieces)
            cc = sum(p[1] for p in pieces) / len(pieces)
            old_d = abs(r - cr) + abs(c - cc)
            new_d = abs(tr - cr) + abs(tc - cc)
            s += (old_d - new_d) * 10
            return -s
        
        moves.sort(key=move_score)
        
        best_move = moves[0]
        
        if maximizing:
            value = -999999
            for m in moves:
                r, c, tr, tc = m
                new_bd = make_move(bd, r, c, tr, tc, current)
                # Check immediate win
                if is_connected(new_bd, current):
                    return 100000, m
                v, _ = alphabeta(new_bd, player, depth - 1, alpha, beta, False)
                if v > value:
                    value = v
                    best_move = m
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
                if time.time() - start_time > time_limit:
                    break
            return value, best_move
        else:
            value = 999999
            for m in moves:
                r, c, tr, tc = m
                new_bd = make_move(bd, r, c, tr, tc, current)
                if is_connected(new_bd, current):
                    return -100000, m
                v, _ = alphabeta(new_bd, player, depth - 1, alpha, beta, True)
                if v < value:
                    value = v
                    best_move = m
                beta = min(beta, value)
                if alpha >= beta:
                    break
                if time.time() - start_time > time_limit:
                    break
            return value, best_move
    
    # Iterative deepening
    best_move = None
    moves = get_legal_moves(board, 1)
    
    if not moves:
        # Should not happen if we have pieces
        return "0,0:0,0"
    
    # Check for immediate wins
    for m in moves:
        r, c, tr, tc = m
        new_bd = make_move(board, r, c, tr, tc, 1)
        if is_connected(new_bd, 1):
            return f"{r},{c}:{tr},{tc}"
    
    best_move = moves[0]
    
    for depth in range(1, 20):
        if time.time() - start_time > time_limit * 0.7:
            break
        val, move = alphabeta(board, 1, depth, -999999, 999999, True)
        if move is not None:
            best_move = move
        if abs(val) >= 90000:
            break
    
    r, c, tr, tc = best_move
    return f"{r},{c}:{tr},{tc}"
