
import numpy as np
from collections import deque
import random

def policy(me, opponent):
    size = 19
    board = np.zeros((size, size), dtype=int)
    for r, c in me:
        board[r-1, c-1] = 1
    for r, c in opponent:
        board[r-1, c-1] = 2
    
    # Precompute groups and liberties
    group_id = np.zeros((size, size), dtype=int)
    group_data = {}
    visited = np.zeros((size, size), dtype=bool)
    gid = 1
    for r in range(size):
        for c in range(size):
            if board[r, c] != 0 and not visited[r, c]:
                color = board[r, c]
                q = deque([(r, c)])
                visited[r, c] = True
                stones = set()
                liberties = set()
                while q:
                    cr, cc = q.popleft()
                    stones.add((cr, cc))
                    group_id[cr, cc] = gid
                    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                        nr, nc = cr+dr, cc+dc
                        if 0 <= nr < size and 0 <= nc < size:
                            if board[nr, nc] == 0:
                                liberties.add((nr, nc))
                            elif board[nr, nc] == color and not visited[nr, nc]:
                                visited[nr, nc] = True
                                q.append((nr, nc))
                group_data[gid] = {
                    'color': color,
                    'size': len(stones),
                    'liberties': liberties
                }
                gid += 1
    
    def neighbors(r, c):
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            if 0 <= nr < size and 0 <= nc < size:
                yield nr, nc
    
    def is_legal(r, c, color):
        if board[r, c] != 0:
            return False
        opponent = 3 - color
        adj_friendly = []
        adj_opponent = []
        empty_neighbors = 0
        for nr, nc in neighbors(r, c):
            if board[nr, nc] == color:
                gid = group_id[nr, nc]
                if gid not in adj_friendly:
                    adj_friendly.append(gid)
            elif board[nr, nc] == opponent:
                gid = group_id[nr, nc]
                if gid not in adj_opponent:
                    adj_opponent.append(gid)
            else:
                empty_neighbors += 1
        
        # Check if any friendly group has liberties other than (r,c)
        for gid in adj_friendly:
            libs = group_data[gid]['liberties']
            if len(libs - {(r, c)}) > 0:
                return True
        # Check if we can capture an opponent group
        for gid in adj_opponent:
            libs = group_data[gid]['liberties']
            if len(libs) == 1 and (r, c) in libs:
                return True
        # New stone not adjacent to any friendly group
        if not adj_friendly:
            if empty_neighbors > 0:
                return True
            return False
        # All friendly groups have exactly this move as their only liberty and no capture
        return False
    
    legal_moves = []
    for r in range(size):
        for c in range(size):
            if is_legal(r, c, 1):
                legal_moves.append((r, c))
    
    if not legal_moves:
        return (0, 0)
    
    # 1. Capture opponent stones
    capture_moves = []
    for move in legal_moves:
        r, c = move
        captured = 0
        for nr, nc in neighbors(r, c):
            if board[nr, nc] == 2:
                gid = group_id[nr, nc]
                libs = group_data[gid]['liberties']
                if len(libs) == 1 and (r, c) in libs:
                    captured += group_data[gid]['size']
        if captured > 0:
            capture_moves.append((move, captured))
    if capture_moves:
        best = max(capture_moves, key=lambda x: (x[1], random.random()))
        return (best[0][0]+1, best[0][1]+1)
    
    # 2. Save own stones in atari
    atari_saves = []
    for gid, data in group_data.items():
        if data['color'] == 1 and len(data['liberties']) == 1:
            lib = next(iter(data['liberties']))
            if is_legal(lib[0], lib[1], 1):
                atari_saves.append((lib, data['size']))
    if atari_saves:
        best = max(atari_saves, key=lambda x: (x[1], random.random()))
        return (best[0][0]+1, best[0][1]+1)
    
    # 3. Put opponent stones in atari
    atari_threats = []
    for gid, data in group_data.items():
        if data['color'] == 2 and len(data['liberties']) == 2:
            for lib in data['liberties']:
                if is_legal(lib[0], lib[1], 1):
                    atari_threats.append((lib, data['size']))
    if atari_threats:
        best = max(atari_threats, key=lambda x: (x[1], random.random()))
        return (best[0][0]+1, best[0][1]+1)
    
    # 4. Heuristic evaluation of remaining moves
    scores = []
    for move in legal_moves:
        r, c = move
        score = 0
        friends = 0
        foes = 0
        adj_friendly_groups = set()
        for nr, nc in neighbors(r, c):
            if board[nr, nc] == 1:
                friends += 1
                adj_friendly_groups.add(group_id[nr, nc])
            elif board[nr, nc] == 2:
                foes += 1
        score += friends * 10
        score += foes * 5
        
        # Corner/edge bonus
        if r in (0, 18) and c in (0, 18):
            score += 50
        elif r in (0, 18) or c in (0, 18):
            score += 30
        else:
            score += 10
        
        # Connection bonus
        if len(adj_friendly_groups) > 1:
            score += len(adj_friendly_groups) * 20
        
        # Self-atari penalty
        if adj_friendly_groups:
            combined_liberties = set()
            for gid in adj_friendly_groups:
                combined_liberties.update(group_data[gid]['liberties'])
            combined_liberties.discard((r, c))
            for nr, nc in neighbors(r, c):
                if board[nr, nc] == 0:
                    combined_liberties.add((nr, nc))
            if len(combined_liberties) == 1:
                score -= 50
        else:
            empty_count = 0
            for nr, nc in neighbors(r, c):
                if board[nr, nc] == 0:
                    empty_count += 1
            if empty_count == 1:
                score -= 50
        
        # Small random tie-break
        score += random.random() * 0.1
        scores.append((move, score))
    
    best = max(scores, key=lambda x: x[1])
    return (best[0][0]+1, best[0][1]+1)
