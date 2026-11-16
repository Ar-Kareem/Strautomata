
import random

_last_board = None
_pattern_shots = None
_clusters = []

def policy(board):
    global _last_board, _pattern_shots, _clusters

    if _last_board is None:
        _last_board = board
        pattern_shots = []
        for r in range(10):
            for c in range(10):
                if (r + c) % 2 == 0:
                    pattern_shots.append((r, c))
        _pattern_shots = pattern_shots
        _clusters = []
    
    new_hits = []
    if _last_board is not None:
        for r in range(10):
            for c in range(10):
                if _last_board[r][c] != 1 and board[r][c] == 1:
                    new_hits.append((r, c))
    
    for hit in new_hits:
        found = False
        for cluster in _clusters:
            for h in cluster['hits']:
                if abs(h[0] - hit[0]) + abs(h[1] - hit[1]) == 1:
                    cluster['hits'].append(hit)
                    found = True
                    break
            if found:
                break
        if not found:
            _clusters.append({
                'hits': [hit],
                'targets': []
            })
    
    for cluster in _clusters:
        if len(cluster['hits']) == 1:
            r, c = cluster['hits'][0]
            targets = []
            for dr, dc in [(0,1), (0,-1), (1,0), (-1,0)]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                    targets.append((nr, nc))
            cluster['targets'] = targets
        else:
            rows = set(r for (r,c) in cluster['hits'])
            cols = set(c for (r,c) in cluster['hits'])
            if len(rows) == 1:
                r = list(rows)[0]
                cols_list = [c for (r_temp, c) in cluster['hits'] if r_temp == r]
                min_col = min(cols_list)
                max_col = max(cols_list)
                targets = []
                if min_col > 0:
                    candidate = (r, min_col-1)
                    if board[r][min_col-1] == 0:
                        targets.append(candidate)
                if max_col < 9:
                    candidate = (r, max_col+1)
                    if board[r][max_col+1] == 0:
                        targets.append(candidate)
                cluster['targets'] = targets
            else:
                c = list(cols)[0]
                rows_list = [r for (r, c_temp) in cluster['hits'] if c_temp == c]
                min_row = min(rows_list)
                max_row = max(rows_list)
                targets = []
                if min_row > 0:
                    candidate = (min_row-1, c)
                    if board[min_row-1][c] == 0:
                        targets.append(candidate)
                if max_row < 9:
                    candidate = (max_row+1, c)
                    if board[max_row+1][c] == 0:
                        targets.append(candidate)
                cluster['targets'] = targets
    
    new_pattern_shots = []
    for shot in _pattern_shots:
        r, c = shot
        if board[r][c] == 0:
            new_pattern_shots.append(shot)
    _pattern_shots = new_pattern_shots
    
    _clusters.sort(key=lambda cl: (len(cl['hits']), -len(cl['targets'])), reverse=True)
    
    if _clusters and _clusters[0]['targets']:
        shot = _clusters[0]['targets'][0]
    elif _pattern_shots:
        shot = _pattern_shots[0]
    else:
        available = [(r,c) for r in range(10) for c in range(10) if board[r][c] == 0]
        if available:
            shot = available[0]
        else:
            shot = (0,0)
    
    _last_board = board
    return shot
