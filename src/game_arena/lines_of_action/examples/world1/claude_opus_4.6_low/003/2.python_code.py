
import numpy as np
from collections import deque

def policy(board):
    board = np.array(board)
    
    def get_moves(b, player):
        moves = []
        pieces = list(zip(*np.where(b == player)))
        for r, c in pieces:
            for dr, dc in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
                # count pieces in line
                count = 0
                for i in range(8):
                    if dr == 0 and dc == 0:
                        break
                    if dr == 0:
                        nr, nc = r, i
                    elif dc == 0:
                        nr, nc = i, c
                    else:
                        # diagonal
                        nr, nc = r + (i - _get_start(r, c, dr, dc)), c + (i - _get_start(r, c, dr, dc)) * dc // abs(dc) if dc != 0 else c
                # Simpler approach
                count = count_in_line(b, r, c, dr, dc)
                tr, tc = r + dr*count, c + dc*count
                if 0 <= tr < 8 and 0 <= tc < 8:
                    if b[tr, tc] != player:
                        # check no enemy in path
                        blocked = False
                        for step in range(1, count):
                            mr, mc = r + dr*step, c + dc*step
                            if b[mr, mc] == -player:
                                blocked = True
                                break
                        if not blocked:
                            moves.append((r, c, tr, tc))
        return moves

    def count_in_line(b, r, c, dr, dc):
        count = 0
        if dr == 0 and dc == 0:
            return 0
        # Count all pieces along the entire line through (r,c) in direction (dr,dc)
        # Find the full line
        pieces_on_line = 0
        if dc == 0:  # vertical
            for i in range(8):
                if b[i, c] != 0:
                    pieces_on_line += 1
        elif dr == 0:  # horizontal
            for i in range(8):
                if b[r, i] != 0:
                    pieces_on_line += 1
        else:  # diagonal
            # go to start of diagonal
            sr, sc = r, c
            while sr - dr >= 0 and sr - dr < 8 and sc - dc >= 0 and sc - dc < 8:
                sr -= dr
                sc -= dc
            while 0 <= sr < 8 and 0 <= sc < 8:
                if b[sr, sc] != 0:
                    pieces_on_line += 1
                sr += dr
                sc += dc
        return pieces_on_line

    def connected_components(b, player):
        pieces = set(zip(*np.where(b == player)))
        if not pieces:
            return 0
        visited = set()
        components = 0
        for p in pieces:
            if p not in visited:
                components += 1
                q = deque([p])
                while q:
                    cr, cc = q.popleft()
                    if (cr, cc) in visited:
                        continue
                    visited.add((cr, cc))
                    for dr in [-1,0,1]:
                        for dc in [-1,0,1]:
                            if dr==0 and dc==0: continue
                            nr, nc = cr+dr, cc+dc
                            if (nr,nc) in pieces and (nr,nc) not in visited:
                                q.append((nr,nc))
        return components

    def evaluate(b):
        my_comp = connected_components(b, 1)
        opp_comp = connected_components(b, -1)
        if my_comp == 1:
            return 10000
        if opp_comp == 1:
            return -10000
        # center of mass spread
        my_pieces = np.argwhere(b == 1).astype(float)
        if len(my_pieces) == 0:
            return -10000
        center = my_pieces.mean(axis=0)
        my_spread = np.sum((my_pieces - center)**2)
        
        opp_pieces = np.argwhere(b == -1).astype(float)
        if len(opp_pieces) == 0:
            return 10000
        opp_center = opp_pieces.mean(axis=0)
        opp_spread = np.sum((opp_pieces - opp_center)**2)
        
        return -my_comp * 50 - my_spread + opp_comp * 30 + opp_spread * 0.5

    def minimax(b, depth, alpha, beta, maximizing):
        player = 1 if maximizing else -1
        if depth == 0:
            return evaluate(b), None
        moves = get_moves(b, player)
        if not moves:
            return evaluate(b), None
        
        best_move = moves[0]
        if maximizing:
            val = -float('inf')
            for m in moves:
                nb = b.copy()
                nb[m[2], m[3]] = player
                nb[m[0], m[1]] = 0
                v, _ = minimax(nb, depth-1, alpha, beta, False)
                if v > val:
                    val = v
                    best_move = m
                alpha = max(alpha, v)
                if beta <= alpha:
                    break
            return val, best_move
        else:
            val = float('inf')
            for m in moves:
                nb = b.copy()
                nb[m[2], m[3]] = player
                nb[m[0], m[1]] = 0
                v, _ = minimax(nb, depth-1, alpha, beta, True)
                if v < val:
                    val = v
                    best_move = m
                beta = min(beta, v)
                if beta <= alpha:
                    break
            return val, best_move

    moves = get_moves(board, 1)
    if not moves:
        # shouldn't happen
        return "0,0:0,0"
    
    # Check for immediate win
    for m in moves:
        nb = board.copy()
        nb[m[2], m[3]] = 1
        nb[m[0], m[1]] = 0
        if connected_components(nb, 1) == 1:
            return f"{m[0]},{m[1]}:{m[2]},{m[3]}"
    
    _, best = minimax(board, 3, -float('inf'), float('inf'), True)
    if best is None:
        best = moves[0]
    return f"{best[0]},{best[1]}:{best[2]},{best[3]}"
