
import math

def policy(me, opponent, memory):
    current_opponent_before_move = opponent.copy()
    
    ko_info = {}
    if memory:
        prev_opponent = memory.get('prev_opponent', [])
        my_last_move = memory.get('my_last_move', None)
        last_captured = [stone for stone in prev_opponent if stone not in opponent]
        ko_info = {'last_move': my_last_move, 'last_captured': last_captured}
    
    all_stones = set(me) | set(opponent)
    empty_positions = [(i, j) for i in range(1, 20) for j in range(1, 20) if (i, j) not in all_stones]
    
    if not empty_positions:
        return ((0, 0), {'prev_opponent': current_opponent_before_move, 'my_last_move': None, 'last_captured': []})
    
    def is_legal(move):
        new_me = me + [move]
        new_all_stones = set(new_me) | set(opponent)
        stack = [move]
        visited = set()
        liberties = set()
        while stack:
            i, j = stack.pop()
            if (i, j) in visited:
                continue
            visited.add((i, j))
            for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                ni, nj = i + di, j + dj
                if 1 <= ni <= 19 and 1 <= nj <= 19:
                    if (ni, nj) not in new_all_stones:
                        liberties.add((ni, nj))
                    elif (ni, nj) in new_me and (ni, nj) not in visited:
                        stack.append((ni, nj))
        if len(liberties) >= 1:
            return True
        
        for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ni, nj = move[0] + di, move[1] + dj
            if (ni, nj) in opponent:
                group_stack = [(ni, nj)]
                group_visited = set()
                is_captured = True
                while group_stack:
                    gi, gj = group_stack.pop()
                    if (gi, gj) in group_visited:
                        continue
                    group_visited.add((gi, gj))
                    for gdi, gdj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        gni, gnj = gi + gdi, gj + gdj
                        if 1 <= gni <= 19 and 1 <= gnj <= 19:
                            if (gni, gnj) not in new_all_stones:
                                is_captured = False
                                break
                            elif (gni, gnj) in opponent and (gni, gnj) not in group_visited:
                                group_stack.append((gni, gnj))
                    if not is_captured:
                        break
                if is_captured:
                    return True
        return False
    
    def compute_capture(move):
        new_me = me + [move]
        new_all_stones = set(new_me) | set(opponent)
        captured = set()
        for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ni, nj = move[0] + di, move[1] + dj
            if (ni, nj) in opponent:
                group_stack = [(ni, nj)]
                group_visited = set()
                is_captured = True
                while group_stack:
                    gi, gj = group_stack.pop()
                    if (gi, gj) in group_visited:
                        continue
                    group_visited.add((gi, gj))
                    for gdi, gdj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        gni, gnj = gi + gdi, gj + gdj
                        if 1 <= gni <= 19 and 1 <= gnj <= 19:
                            if (gni, gnj) not in new_all_stones:
                                is_captured = False
                                break
                            elif (gni, gnj) in opponent and (gni, gnj) not in group_visited:
                                group_stack.append((gni, gnj))
                    if not is_captured:
                        break
                if is_captured:
                    captured.update(group_visited)
        return list(captured)
    
    def evaluate_move(move):
        captured = len(compute_capture(move))
        distance = abs(move[0] - 10) + abs(move[1] - 10)
        centrality = 36 - distance
        
        adj_atari = 0
        for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ni, nj = move[0] + di, move[1] + dj
            if (ni, nj) in opponent:
                group_stack = [(ni, nj)]
                group_visited = set()
                liberties = set()
                all_stones = set(me) | set(opponent)
                while group_stack:
                    gi, gj = group_stack.pop()
                    if (gi, gj) in group_visited:
                        continue
                    group_visited.add((gi, gj))
                    for gdi, gdj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        gni, gnj = gi + gdi, gj + gdj
                        if 1 <= gni <= 19 and 1 <= gnj <= 19:
                            if (gni, gnj) not in all_stones:
                                liberties.add((gni, gnj))
                            elif (gni, gnj) in opponent and (gni, gnj) not in group_visited:
                                group_stack.append((gni, gnj))
                if len(liberties) == 1:
                    adj_atari += 1
        
        return 100 * captured + centrality + 50 * adj_atari
    
    legal_moves = []
    for move in empty_positions:
        if ko_info.get('last_move') == move and len(ko_info.get('last_captured', [])) == 1:
            if ko_info['last_captured'][0] in opponent:
                continue
        if is_legal(move):
            legal_moves.append(move)
    
    if not legal_moves:
        return ((0, 0), {'prev_opponent': current_opponent_before_move, 'my_last_move': None, 'last_captured': []})
    
    scored_moves = [(evaluate_move(move), move) for move in legal_moves]
    scored_moves.sort(reverse=True, key=lambda x: x[0])
    best_move = scored_moves[0][1]
    
    captured = compute_capture(best_move)
    
    new_memory = {
        'prev_opponent': current_opponent_before_move,
        'my_last_move': best_move,
        'last_captured': captured
    }
    
    return (best_move, new_memory)
