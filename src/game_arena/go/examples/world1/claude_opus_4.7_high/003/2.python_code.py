
import random

SIZE = 19

def neighbors(r, c):
    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
        nr, nc = r+dr, c+dc
        if 1 <= nr <= SIZE and 1 <= nc <= SIZE:
            yield nr, nc

def diagonals(r, c):
    for dr, dc in [(-1,-1),(-1,1),(1,-1),(1,1)]:
        nr, nc = r+dr, c+dc
        if 1 <= nr <= SIZE and 1 <= nc <= SIZE:
            yield nr, nc

def get_group(board, r, c):
    color = board.get((r,c))
    if color is None:
        return set(), set()
    group = {(r,c)}
    libs = set()
    stack = [(r,c)]
    while stack:
        x,y = stack.pop()
        for nx,ny in neighbors(x,y):
            v = board.get((nx,ny))
            if v is None:
                libs.add((nx,ny))
            elif v == color and (nx,ny) not in group:
                group.add((nx,ny))
                stack.append((nx,ny))
    return group, libs

def play(board, r, c, color):
    if (r,c) in board:
        return None, 0
    nb = dict(board)
    nb[(r,c)] = color
    opp = -color
    captured = 0
    visited = set()
    for nr,nc in neighbors(r,c):
        if nb.get((nr,nc)) == opp and (nr,nc) not in visited:
            grp, libs = get_group(nb, nr, nc)
            visited |= grp
            if not libs:
                for s in grp:
                    del nb[s]
                captured += len(grp)
    grp, libs = get_group(nb, r, c)
    if not libs:
        return None, 0
    return nb, captured

def is_true_eye(board, r, c, color):
    for n in neighbors(r,c):
        if board.get(n) != color:
            return False
    diag_opp = 0
    diag_total = 0
    for n in diagonals(r,c):
        diag_total += 1
        if board.get(n) == -color:
            diag_opp += 1
    edge_diag = 4 - diag_total
    if edge_diag > 0:
        return diag_opp == 0
    return diag_opp <= 1

def policy(me, opponent):
    board = {}
    for s in me: board[tuple(s)] = 1
    for s in opponent: board[tuple(s)] = -1
    
    total_stones = len(me) + len(opponent)
    
    if total_stones < 8:
        opening = [(4,4),(16,16),(4,16),(16,4),(10,10),(4,10),(16,10),(10,4),(10,16)]
        for mv in opening:
            if mv not in board:
                res, _ = play(board, mv[0], mv[1], 1)
                if res is not None:
                    return mv
    
    my_groups = []
    opp_groups = []
    seen = set()
    for pos,col in list(board.items()):
        if pos in seen: continue
        grp, libs = get_group(board, pos[0], pos[1])
        seen |= grp
        if col == 1:
            my_groups.append((grp, libs))
        else:
            opp_groups.append((grp, libs))
    
    candidates = set()
    for (r,c) in board:
        for dr in range(-2,3):
            for dc in range(-2,3):
                nr,nc = r+dr, c+dc
                if 1<=nr<=SIZE and 1<=nc<=SIZE and (nr,nc) not in board:
                    candidates.add((nr,nc))
    
    if not candidates:
        return (10,10)
    
    best_score = -1e18
    best_move = (0,0)
    
    for (r,c) in candidates:
        if is_true_eye(board, r, c, 1):
            continue
        res, cap = play(board, r, c, 1)
        if res is None:
            continue
        
        score = 0.0
        score += cap * 25
        
        my_grp, my_libs = get_group(res, r, c)
        score += min(len(my_libs), 6) * 2
        score += min(len(my_grp), 8) * 0.3
        
        # Atari save check
        for g, l in my_groups:
            if len(l) == 1:
                adj = any(nb_pos in g for nb_pos in neighbors(r,c))
                if adj:
                    if len(my_libs) >= 2:
                        score += 40
                    else:
                        score -= 20
        
        # Atari threat on opponent
        for g, l in opp_groups:
            adj = any(nb_pos in g for nb_pos in neighbors(r,c))
            if adj:
                before_libs = len(l)
                # recompute after move
                # find one stone of g still in res
                remaining = [s for s in g if s in res]
                if remaining:
                    _, new_libs = get_group(res, remaining[0][0], remaining[0][1])
                    after = len(new_libs)
                    if after == 1:
                        score += 15 + len(g) * 2
                    elif after == 2:
                        score += 5 + len(g)
                    score += max(0, before_libs - after) * 3
        
        # Edge preference
        min_edge = min(r-1, SIZE-r, c-1, SIZE-c)
        if min_edge == 0:
            score -= 8
        elif min_edge == 1:
            score -= 2
        elif min_edge in (2,3):
            score += 2
        elif min_edge == 4:
            score += 1
        
        near_my = sum(1 for n in neighbors(r,c) if board.get(n) == 1)
        near_opp = sum(1 for n in neighbors(r,c) if board.get(n) == -1)
        score += near_my * 0.4 + near_opp * 0.8
        
        # Self-atari penalty (playing into atari)
        if len(my_libs) == 1 and cap == 0:
            score -= 30
        
        score += random.random() * 0.05
        
        if score > best_score:
            best_score = score
            best_move = (r,c)
    
    if best_move == (0,0):
        for r in range(1,SIZE+1):
            for c in range(1,SIZE+1):
                if (r,c) not in board:
                    if is_true_eye(board, r, c, 1):
                        continue
                    res,_ = play(board,r,c,1)
                    if res is not None:
                        return (r,c)
        return (0,0)
    
    return best_move
