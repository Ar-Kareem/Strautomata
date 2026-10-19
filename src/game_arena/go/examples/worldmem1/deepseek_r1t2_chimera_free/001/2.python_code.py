
import copy
from collections import deque

def find_groups(board):
    visited = set()
    my_groups = []
    opp_groups = []
    for r in range(1, 20):
        for c in range(1, 20):
            if (r, c) in visited:
                continue
            val = board[r][c]
            if val == 1 or val == -1:
                queue = deque([(r, c)])
                stones = set()
                liberties = set()
                while queue:
                    rr, cc = queue.popleft()
                    if (rr, cc) in stones:
                        continue
                    stones.add((rr, cc))
                    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                        nr, nc = rr + dr, cc + dc
                        if 1 <= nr <= 19 and 1 <= nc <= 19:
                            if board[nr][nc] == 0:
                                liberties.add((nr, nc))
                            elif board[nr][nc] == val and (nr, nc) not in stones:
                                queue.append((nr, nc))
                visited.update(stones)
                group_data = {
                    'stones': stones,
                    'liberties': liberties,
                    'liberty_count': len(liberties),
                    'liberty_points': liberties
                }
                if val == 1:
                    my_groups.append(group_data)
                else:
                    opp_groups.append(group_data)
    return {'my_groups': my_groups, 'opponent_groups': opp_groups}

def is_legal_move(board, r, c, player):
    if board[r][c] != 0:
        return False
    
    temp_board = copy.deepcopy(board)
    temp_board[r][c] = player
    opponent = -1 if player == 1 else 1
    
    captured = False
    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
        nr, nc = r + dr, c + dc
        if 1 <= nr <= 19 and 1 <= nc <= 19 and temp_board[nr][nc] == opponent:
            visited = set()
            queue = deque([(nr, nc)])
            group_stones = set()
            has_liberty = False
            while queue:
                rr, cc = queue.popleft()
                if (rr, cc) in visited:
                    continue
                visited.add((rr, cc))
                group_stones.add((rr, cc))
                for dr2, dc2 in [(-1,0),(1,0),(0,-1),(0,1)]:
                    ar, ac = rr + dr2, cc + dc2
                    if 1 <= ar <= 19 and 1 <= ac <= 19:
                        if temp_board[ar][ac] == 0:
                            has_liberty = True
                        elif temp_board[ar][ac] == opponent and (ar, ac) not in visited:
                            queue.append((ar, ac))
            if not has_liberty and len(group_stones) > 0:
                captured = True
    if captured:
        return True
    
    has_liberty = False
    visited = set()
    queue = deque([(r, c)])
    while queue:
        rr, cc = queue.popleft()
        if (rr, cc) in visited:
            continue
        visited.add((rr, cc))
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = rr + dr, cc + dc
            if 1 <= nr <= 19 and 1 <= nc <= 19:
                if temp_board[nr][nc] == 0:
                    has_liberty = True
                    queue = deque()
                    break
                elif temp_board[nr][nc] == player and (nr, nc) not in visited:
                    queue.append((nr, nc))
    
    return has_liberty

def policy(me, opponent, memory):
    if 'move_count' not in memory:
        memory['move_count'] = 0
        memory['opening_moves'] = [(4,4), (16,16), (4,16), (16,4), (10,10)]
    
    move_count = memory['move_count']
    memory['move_count'] += 1
    
    board = [[0]*20 for _ in range(20)]
    for r, c in me:
        board[r][c] = 1
    for r, c in opponent:
        board[r][c] = -1
    
    if move_count < len(memory['opening_moves']):
        for move in memory['opening_moves']:
            r, c = move
            if board[r][c] == 0:
                return (move, memory)
    
    groups = find_groups(board)
    my_groups = groups['my_groups']
    opp_groups = groups['opponent_groups']
    
    capture_moves = []
    for group in opp_groups:
        if group['liberty_count'] == 1:
            (liberty,) = group['liberty_points']
            r, c = liberty
            if is_legal_move(board, r, c, 1):
                capture_moves.append((liberty, len(group['stones'])))
    if capture_moves:
        best_move = max(capture_moves, key=lambda x: x[1])[0]
        return (best_move, memory)
    
    defense_moves = []
    for group in my_groups:
        if group['liberty_count'] == 1:
            (liberty,) = group['liberty_points']
            r, c = liberty
            if is_legal_move(board, r, c, 1):
                defense_moves.append((liberty, len(group['stones'])))
    if defense_moves:
        best_move = max(defense_moves, key=lambda x: x[1])[0]
        return (best_move, memory)
    
    candidate_points = []
    all_stones = set(me) | set(opponent)
    for r in range(1, 20):
        for c in range(1, 20):
            if board[r][c] == 0:
                adjacent = any(1 <= r + dr <=19 and 1 <= c + dc <=19 and board[r+dr][c+dc] != 0
                               for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)])
                if adjacent:
                    candidate_points.append((r, c))
    
    legal_moves = []
    for point in candidate_points:
        r, c = point
        if is_legal_move(board, r, c, 1):
            score = 0
            for dr in range(-3, 4):
                for dc in range(-3, 4):
                    nr = r + dr
                    nc = c + dc
                    if 1 <= nr <=19 and 1 <= nc <=19:
                        dist = abs(dr) + abs(dc)
                        if board[nr][nc] == 1:
                            score += 4 - dist
                        elif board[nr][nc] == -1:
                            score -= 3 - dist
            center_score = 30 - (abs(r-10) + abs(c-10))
            score += center_score
            legal_moves.append(( (r,c), score ))
    
    if legal_moves:
        best_move = max(legal_moves, key=lambda x: x[1])[0]
        return (best_move, memory)
    
    return ((0, 0), memory)
