
import numpy as np
import time

DIRECTIONS = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

# Positional weight matrix
WEIGHTS = np.array([
    [100, -20,  10,   5,   5,  10, -20, 100],
    [-20, -50,  -2,  -2,  -2,  -2, -50, -20],
    [ 10,  -2,   1,   1,   1,   1,  -2,  10],
    [  5,  -2,   1,   0,   0,   1,  -2,   5],
    [  5,  -2,   1,   0,   0,   1,  -2,   5],
    [ 10,  -2,   1,   1,   1,   1,  -2,  10],
    [-20, -50,  -2,  -2,  -2,  -2, -50, -20],
    [100, -20,  10,   5,   5,  10, -20, 100],
], dtype=float)

def get_legal_moves(me, opp):
    moves = []
    for r in range(8):
        for c in range(8):
            if me[r][c] or opp[r][c]:
                continue
            if can_flip(me, opp, r, c):
                moves.append((r, c))
    return moves

def can_flip(me, opp, r, c):
    for dr, dc in DIRECTIONS:
        nr, nc = r + dr, c + dc
        found_opp = False
        while 0 <= nr < 8 and 0 <= nc < 8:
            if opp[nr][nc]:
                found_opp = True
                nr += dr
                nc += dc
            elif me[nr][nc] and found_opp:
                return True
            else:
                break
    return False

def do_move(me, opp, r, c):
    new_me = me.copy()
    new_opp = opp.copy()
    new_me[r][c] = 1
    for dr, dc in DIRECTIONS:
        nr, nc = r + dr, c + dc
        to_flip = []
        while 0 <= nr < 8 and 0 <= nc < 8:
            if new_opp[nr][nc]:
                to_flip.append((nr, nc))
                nr += dr
                nc += dc
            elif new_me[nr][nc] and to_flip:
                for fr, fc in to_flip:
                    new_me[fr][fc] = 1
                    new_opp[fr][fc] = 0
                break
            else:
                break
    return new_me, new_opp

def evaluate(me, opp):
    my_count = int(np.sum(me))
    opp_count = int(np.sum(opp))
    total = my_count + opp_count
    empties = 64 - total
    
    # Terminal state
    my_moves = get_legal_moves(me, opp)
    opp_moves = get_legal_moves(opp, me)
    
    if not my_moves and not opp_moves:
        if my_count > opp_count:
            return 10000 + (my_count - opp_count)
        elif my_count < opp_count:
            return -10000 - (opp_count - my_count)
        else:
            return 0
    
    score = 0.0
    
    # Positional
    score += float(np.sum(me * WEIGHTS) - np.sum(opp * WEIGHTS))
    
    # Corner occupancy
    corners = [(0,0),(0,7),(7,0),(7,7)]
    my_corners = sum(me[r][c] for r,c in corners)
    opp_corners = sum(opp[r][c] for r,c in corners)
    score += 25 * (my_corners - opp_corners)
    
    # Adjust weights near taken corners
    for cr, cc in corners:
        if me[cr][cc] or opp[cr][cc]:
            # If corner is taken, adjacent squares are no longer bad
            adj = []
            if cr == 0 and cc == 0:
                adj = [(0,1),(1,0),(1,1)]
            elif cr == 0 and cc == 7:
                adj = [(0,6),(1,6),(1,7)]
            elif cr == 7 and cc == 0:
                adj = [(6,0),(6,1),(7,1)]
            elif cr == 7 and cc == 7:
                adj = [(6,6),(6,7),(7,6)]
    
    # Mobility
    my_mob = len(my_moves)
    opp_mob = len(opp_moves)
    if my_mob + opp_mob > 0:
        score += 10 * (my_mob - opp_mob) / (my_mob + opp_mob + 1)
    
    # Disc parity (more important in endgame)
    if empties < 15:
        score += 3 * (my_count - opp_count)
    else:
        # In midgame, fewer discs can be better
        score += -0.5 * (my_count - opp_count)
    
    # Frontier (discs adjacent to empty squares are vulnerable)
    my_frontier = 0
    opp_frontier = 0
    for r in range(8):
        for c in range(8):
            if me[r][c] or opp[r][c]:
                is_me = me[r][c] == 1
                for dr, dc in DIRECTIONS:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < 8 and 0 <= nc < 8 and not me[nr][nc] and not opp[nr][nc]:
                        if is_me:
                            my_frontier += 1
                        else:
                            opp_frontier += 1
                        break
    if my_frontier + opp_frontier > 0:
        score -= 3 * (my_frontier - opp_frontier) / (my_frontier + opp_frontier + 1)
    
    return score

def alphabeta(me, opp, depth, alpha, beta, maximizing, deadline):
    if time.time() > deadline:
        raise TimeoutError
    
    my_moves = get_legal_moves(me, opp)
    opp_moves_exist = bool(get_legal_moves(opp, me))
    
    if depth == 0:
        return evaluate(me, opp), None
    
    if not my_moves and not opp_moves_exist:
        return evaluate(me, opp), None
    
    if maximizing:
        if not my_moves:
            # Must pass
            val, _ = alphabeta(opp, me, depth - 1, -beta, -alpha, False, deadline)
            return -val, None
        
        # Move ordering: prioritize corners, then edges
        def move_priority(m):
            r, c = m
            if (r, c) in [(0,0),(0,7),(7,0),(7,7)]:
                return 0
            if r == 0 or r == 7 or c == 0 or c == 7:
                return 1
            return 2
        my_moves.sort(key=move_priority)
        
        best_val = -float('inf')
        best_move = my_moves[0]
        for r, c in my_moves:
            new_me, new_opp = do_move(me, opp, r, c)
            val, _ = alphabeta(new_opp, new_me, depth - 1, -beta, -alpha, False, deadline)
            val = -val
            if val > best_val:
                best_val = val
                best_move = (r, c)
            alpha = max(alpha, val)
            if alpha >= beta:
                break
        return best_val, best_move
    else:
        if not my_moves:
            val, _ = alphabeta(opp, me, depth - 1, -beta, -alpha, True, deadline)
            return -val, None
        
        def move_priority(m):
            r, c = m
            if (r, c) in [(0,0),(0,7),(7,0),(7,7)]:
                return 0
            if r == 0 or r == 7 or c == 0 or c == 7:
                return 1
            return 2
        my_moves.sort(key=move_priority)
        
        best_val = -float('inf')
        best_move = my_moves[0]
        for r, c in my_moves:
            new_me, new_opp = do_move(me, opp, r, c)
            val, _ = alphabeta(new_opp, new_me, depth - 1, -beta, -alpha, True, deadline)
            val = -val
            if val > best_val:
                best_val = val
                best_move = (r, c)
            alpha = max(alpha, val)
            if alpha >= beta:
                break
        return best_val, best_move


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    moves = get_legal_moves(you, opponent)
    if not moves:
        return "pass"
    
    deadline = time.time() + 0.85
    empties = 64 - int(np.sum(you)) - int(np.sum(opponent))
    
    best_move = moves[0]
    
    # Iterative deepening
    max_depth = min(empties, 20)
    
    for depth in range(1, max_depth + 1):
        try:
            val, move = alphabeta(you, opponent, depth, -float('inf'), float('inf'), True, deadline)
            if move is not None:
                best_move = move
        except TimeoutError:
            break
        if time.time() > deadline:
            break
    
    r, c = best_move
    col_letter = chr(ord('a') + c)
    row_number = str(r + 1)
    return col_letter + row_number
