
import numpy as np
from collections import deque
import time

def policy(board) -> str:
    board = np.array(board)
    start_time = time.time()
    
    def get_pieces(b, player):
        return list(zip(*np.where(b == player)))
    
    def count_in_line(b, r, c, dr, dc):
        # Count all pieces along the full line through (r,c) in direction (dr,dc)
        count = 0
        # Go in positive direction from start of line
        if dr == 0 and dc == 0:
            return 0
        # Find all pieces on the line
        # For row: if dr==0, all same row; for col: if dc==0, all same col
        # Easiest: walk both directions
        count = 0
        # count piece at (r,c) itself
        if b[r, c] != 0:
            count += 1
        # positive direction
        nr, nc = r + dr, c + dc
        while 0 <= nr < 8 and 0 <= nc < 8:
            if b[nr, nc] != 0:
                count += 1
            nr += dr
            nc += dc
        # negative direction
        nr, nc = r - dr, c - dc
        while 0 <= nr < 8 and 0 <= nc < 8:
            if b[nr, nc] != 0:
                count += 1
            nr -= dr
            nc -= dc
        return count
    
    def get_legal_moves(b, player):
        moves = []
        pieces = get_pieces(b, player)
        directions = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]
        for r, c in pieces:
            for dr, dc in directions:
                dist = count_in_line(b, r, c, dr, dc)
                tr, tc = r + dr * dist, c + dc * dist
                if not (0 <= tr < 8 and 0 <= tc < 8):
                    continue
                # Check path for enemy pieces (can't jump over enemy)
                blocked = False
                for step in range(1, dist):
                    mr, mc = r + dr * step, c + dc * step
                    if b[mr, mc] == -player:
                        blocked = True
                        break
                if blocked:
                    continue
                # Can't land on own piece
                if b[tr, tc] == player:
                    continue
                moves.append((r, c, tr, tc))
        return moves
    
    def is_connected(b, player):
        pieces = get_pieces(b, player)
        if len(pieces) <= 1:
            return True
        visited = set()
        queue = deque([pieces[0]])
        visited.add(pieces[0])
        piece_set = set(pieces)
        while queue:
            r, c = queue.popleft()
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if (nr, nc) in piece_set and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        queue.append((nr, nc))
        return len(visited) == len(pieces)
    
    def connected_components(b, player):
        pieces = get_pieces(b, player)
        if not pieces:
            return 0, 0
        piece_set = set(pieces)
        visited = set()
        components = 0
        max_size = 0
        for p in pieces:
            if p in visited:
                continue
            components += 1
            size = 0
            queue = deque([p])
            visited.add(p)
            while queue:
                r, c = queue.popleft()
                size += 1
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        if (nr, nc) in piece_set and (nr, nc) not in visited:
                            visited.add((nr, nc))
                            queue.append((nr, nc))
            max_size = max(max_size, size)
        return components, max_size
    
    def evaluate(b):
        # Check wins
        p1 = get_pieces(b, 1)
        pm1 = get_pieces(b, -1)
        
        if len(p1) <= 1 or is_connected(b, 1):
            return 100000
        if len(pm1) <= 1 or is_connected(b, -1):
            return -100000
        
        comp1, max1 = connected_components(b, 1)
        comp_m1, max_m1 = connected_components(b, -1)
        
        # Center of mass distance
        def com_dist(pieces):
            if not pieces:
                return 0
            cr = sum(r for r, c in pieces) / len(pieces)
            cc = sum(c for r, c in pieces) / len(pieces)
            return sum(abs(r - cr) + abs(c - cc) for r, c in pieces)
        
        # Adjacency count
        def adj_count(b, player):
            pieces = set(get_pieces(b, player))
            count = 0
            for r, c in pieces:
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0:
                            continue
                        if (r+dr, c+dc) in pieces:
                            count += 1
            return count // 2
        
        score = 0
        # Components: fewer is better for us
        score += (comp_m1 - comp1) * 50
        # Largest component ratio
        score += (max1 / max(len(p1), 1) - max_m1 / max(len(pm1), 1)) * 40
        # Center of mass
        score += (com_dist(pm1) - com_dist(p1)) * 3
        # Adjacency
        score += (adj_count(b, 1) - adj_count(b, -1)) * 8
        # Piece count advantage (captures help if they reduce opponent connectivity)
        score += (len(p1) - len(pm1)) * 2
        
        return score
    
    def make_move(b, r, c, tr, tc, player):
        nb = b.copy()
        nb[r, c] = 0
        nb[tr, tc] = player
        return nb
    
    def order_moves(b, moves, player):
        scored = []
        pieces = get_pieces(b, player)
        if pieces:
            cr = sum(r for r, c in pieces) / len(pieces)
            cc = sum(c for r, c in pieces) / len(pieces)
        else:
            cr, cc = 3.5, 3.5
        for m in moves:
            r, c, tr, tc = m
            s = 0
            if b[tr, tc] == -player:
                s += 100  # capture
            # Distance to COM reduction
            old_d = abs(r - cr) + abs(c - cc)
            new_d = abs(tr - cr) + abs(tc - cc)
            s += (old_d - new_d) * 5
            scored.append((-s, m))
        scored.sort()
        return [m for _, m in scored]
    
    def minimax(b, depth, alpha, beta, maximizing, deadline):
        if time.time() > deadline:
            return evaluate(b), None
        
        player = 1 if maximizing else -1
        moves = get_legal_moves(b, player)
        
        if depth == 0 or not moves:
            return evaluate(b), None
        
        moves = order_moves(b, moves, player)
        best_move = moves[0]
        
        if maximizing:
            max_eval = -float('inf')
            for m in moves:
                nb = make_move(b, m[0], m[1], m[2], m[3], player)
                ev, _ = minimax(nb, depth - 1, alpha, beta, False, deadline)
                if ev > max_eval:
                    max_eval = ev
                    best_move = m
                alpha = max(alpha, ev)
                if beta <= alpha or time.time() > deadline:
                    break
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for m in moves:
                nb = make_move(b, m[0], m[1], m[2], m[3], player)
                ev, _ = minimax(nb, depth - 1, alpha, beta, True, deadline)
                if ev < min_eval:
                    min_eval = ev
                    best_move = m
                beta = min(beta, ev)
                if beta <= alpha or time.time() > deadline:
                    break
            return min_eval, best_move
    
    deadline = start_time + 0.85
    best_move = None
    
    legal = get_legal_moves(board, 1)
    if not legal:
        return "0,0:0,0"
    
    best_move = legal[0]
    
    # Check for immediate win
    for m in legal:
        nb = make_move(board, m[0], m[1], m[2], m[3], 1)
        if is_connected(nb, 1):
            return f"{m[0]},{m[1]}:{m[2]},{m[3]}"
    
    # Iterative deepening
    for depth in range(1, 10):
        if time.time() > deadline - 0.1:
            break
        ev, mv = minimax(board, depth, -float('inf'), float('inf'), True, deadline - 0.05)
        if mv:
            best_move = mv
        if abs(ev) > 90000:
            break
    
    return f"{best_move[0]},{best_move[1]}:{best_move[2]},{best_move[3]}"
