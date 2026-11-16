
import numpy as np
from collections import deque

def policy(me, opponent, memory):
    # Convert to 0-indexed sets
    my_set = set((r-1, c-1) for r, c in me)
    opp_set = set((r-1, c-1) for r, c in opponent)
    
    # Initialize board (0=empty, 1=me, 2=opponent)
    board = np.zeros((19, 19), dtype=np.int8)
    for r, c in my_set:
        board[r, c] = 1
    for r, c in opp_set:
        board[r, c] = 2
    
    last_board = memory.get('last_board', None)
    move_num = len(me) + len(opponent)
    
    # Opening: if empty, play 4-4 point
    if move_num == 0:
        new_board = board.copy()
        new_board[3, 3] = 1
        memory['last_board'] = new_board
        return ((4, 4), memory)
    
    # Analyze groups
    groups, group_map = _analyze_groups(board)
    
    # Generate candidates (adjacent to stones + fuseki points)
    candidates = set()
    for r, c in (my_set | opp_set):
        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
            nr, nc = r+dr, c+dc
            if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == 0:
                candidates.add((nr, nc))
    
    # If few candidates (early game), add star points
    if len(candidates) < 10:
        for r, c in [(3,3), (3,9), (3,15), (9,3), (9,9), (9,15), (15,3), (15,9), (15,15)]:
            if board[r, c] == 0:
                candidates.add((r, c))
    
    # If still no candidates, scan all empty
    if not candidates:
        for r in range(19):
            for c in range(19):
                if board[r, c] == 0:
                    candidates.add((r, c))
    
    best_move = None
    best_score = -99999
    
    for r, c in candidates:
        # Check legality (suicide and ko)
        if not _is_legal(board, r, c, 1, last_board, groups, group_map):
            continue
        
        score = _evaluate(board, r, c, 1, 2, groups, group_map, move_num)
        
        if score > best_score:
            best_score = score
            best_move = (r, c)
    
    if best_move:
        # Update memory with new board state
        new_board = board.copy()
        new_board[best_move[0], best_move[1]] = 1
        
        # Remove captured stones for ko detection
        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
            nr, nc = best_move[0]+dr, best_move[1]+dc
            if 0 <= nr < 19 and 0 <= nc < 19 and new_board[nr, nc] == 2:
                gid = group_map[nr, nc]
                if gid > 0:
                    g = groups[gid]
                    # Check if this move captured this group
                    if len(g['liberties']) == 1 and (best_move[0], best_move[1]) in g['liberties']:
                        for sr, sc in g['stones']:
                            new_board[sr, sc] = 0
        
        memory['last_board'] = new_board
        return ((best_move[0]+1, best_move[1]+1), memory)
    else:
        return ((0, 0), memory)

def _analyze_groups(board):
    visited = np.zeros((19, 19), dtype=np.int32)
    groups = {}
    group_map = np.full((19, 19), -1, dtype=np.int32)
    gid = 0
    
    for r in range(19):
        for c in range(19):
            if board[r, c] != 0 and visited[r, c] == 0:
                gid += 1
                color = board[r, c]
                stones = []
                liberties = set()
                queue = deque([(r, c)])
                visited[r, c] = gid
                
                while queue:
                    cr, cc = queue.popleft()
                    stones.append((cr, cc))
                    group_map[cr, cc] = gid
                    
                    for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                        nr, nc = cr+dr, cc+dc
                        if 0 <= nr < 19 and 0 <= nc < 19:
                            if board[nr, nc] == 0:
                                liberties.add((nr, nc))
                            elif board[nr, nc] == color and visited[nr, nc] == 0:
                                visited[nr, nc] = gid
                                queue.append((nr, nc))
                
                groups[gid] = {'stones': stones, 'liberties': liberties, 'color': color}
    
    return groups, group_map

def _is_legal(board, r, c, my_color, last_board, groups, group_map):
    if board[r, c] != 0:
        return False
    
    opp_color = 3 - my_color
    captures = False
    has_liberty = False
    
    # Check neighbors
    neighbors = []
    for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
        nr, nc = r+dr, c+dc
        if 0 <= nr < 19 and 0 <= nc < 19:
            neighbors.append((nr, nc))
            if board[nr, nc] == 0:
                has_liberty = True
            elif board[nr, nc] == opp_color:
                gid = group_map[nr, nc]
                if gid > 0 and gid in groups:
                    g = groups[gid]
                    if len(g['liberties']) == 1 and (r, c) in g['liberties']:
                        captures = True
            elif board[nr, nc] == my_color:
                gid = group_map[nr, nc]
                if gid > 0 and gid in groups:
                    g = groups[gid]
                    # Group has other liberties besides this point
                    if len(g['liberties']) > 1 or (len(g['liberties']) == 1 and (r,c) not in g['liberties']):
                        has_liberty = True
    
    # Check suicide
    if not captures and not has_liberty:
        return False
    
    # Check ko
    if last_board is not None:
        new_board = board.copy()
        new_board[r, c] = my_color
        
        # Remove captured opponent stones
        for nr, nc in neighbors:
            if new_board[nr, nc] == opp_color:
                gid = group_map[nr, nc]
                if gid > 0 and gid in groups:
                    g = groups[gid]
                    if len(g['liberties']) == 1 and (r, c) in g['liberties']:
                        for sr, sc in g['stones']:
                            new_board[sr, sc] = 0
        
        if np.array_equal(new_board, last_board):
            return False
    
    return True

def _evaluate(board, r, c, my_color, opp_color, groups, group_map, move_num):
    score = 0
    
    # Immediate captures (highest priority)
    for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
        nr, nc = r+dr, c+dc
        if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == opp_color:
            gid = group_map[nr, nc]
            if gid > 0 and gid in groups:
                g = groups[gid]
                if len(g['liberties']) == 1 and (r,c) in g['liberties']:
                    score += 1000 * len(g['stones'])
    
    # Saving own stones in atari
    for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
        nr, nc = r+dr, c+dc
        if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == my_color:
            gid = group_map[nr, nc]
            if gid > 0 and gid in groups:
                g = groups[gid]
                if len(g['liberties']) == 1:
                    # This is the only liberty - filling it saves the group
                    if (r,c) in g['liberties']:
                        score += 500 * len(g['stones'])
    
    # Avoid self-atari (unless capturing)
    if score < 1000:
        my_libs = 0
        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
            nr, nc = r+dr, c+dc
            if 0 <= nr < 19 and 0 <= nc < 19:
                if board[nr, nc] == 0:
                    my_libs += 1
                elif board[nr, nc] == my_color:
                    gid = group_map[nr, nc]
                    if gid > 0 and gid in groups:
                        g = groups[gid]
                        if len(g['liberties']) <= 2:
                            # Connecting to weak group
                            pass
        
        if my_libs <= 1:
            score -= 200
    
    # Positional bonuses
    if move_num < 50:
        # Favor corners and sides in opening
        dist_corner = min(r, 18-r) + min(c, 18-c)
        if dist_corner <= 3:
            score += 50
        elif dist_corner <= 6:
            score += 30
        elif dist_corner <= 9:
            score += 10
    else:
        # Middle game: connectivity
        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
            nr, nc = r+dr, c+dc
            if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == my_color:
                score += 5
    
    return score
