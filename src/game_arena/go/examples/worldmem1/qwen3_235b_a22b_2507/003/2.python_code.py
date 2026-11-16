
import numpy as np
from collections import deque
import hashlib

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    # Board size
    SIZE = 19

    # Convert input to sets for fast lookup
    my_stones = set(me)
    opp_stones = set(opponent)
    all_stones = my_stones | opp_stones

    # Helper: get neighbors
    def neighbors(r, c):
        return [(nr, nc) for nr, nc in [(r-1, c), (r+1, c), (r, c-1), (r, c+1)] 
                if 1 <= nr <= SIZE and 1 <= nc <= SIZE]

    # Helper: find group and liberties using BFS
    def get_group_and_liberties(r, c):
        color = (r, c) in my_stones
        stone_set = my_stones if color else opp_stones
        group = set()
        visited = set()
        lib_set = set()
        queue = deque([(r, c)])
        visited.add((r, c))
        
        while queue:
            cr, cc = queue.popleft()
            group.add((cr, cc))
            for nr, nc in neighbors(cr, cc):
                if (nr, nc) not in all_stones:
                    lib_set.add((nr, nc))
                elif (nr, nc) not in visited and (nr, nc) in stone_set:
                    visited.add((nr, nc))
                    queue.append((nr, nc))
        return group, lib_set

    # Check if move is legal (including Ko)
    def is_legal_move(r, c):
        if (r, c) in all_stones:
            return False
        # Play move temporarily
        new_my_stones = my_stones | {(r, c)}
        # Check for self-atari (unless it captures)
        new_liberties = set()
        for nr, nc in neighbors(r, c):
            if (nr, nc) in opp_stones:
                group, libs = get_group_and_liberties(nr, nc)
                if len(libs) == 1 and (r, c) in libs:  # This move would capture
                    return True  # Capture is legal
        # Now check if own group has liberties
        own_group = {(r, c)}
        own_liberties = set()
        for nr, nc in neighbors(r, c):
            if (nr, nc) in new_my_stones and (nr, nc) != (r, c):
                # Merge with adjacent friendly stones
                grp, libs = get_group_and_liberties(nr, nc)
                own_group |= grp
                own_liberties |= libs
            elif (nr, nc) not in all_stones:
                own_liberties.add((nr, nc))
        if not own_liberties:
            return False
        # Check for Ko: would this recreate a previous board state?
        new_board = sorted(new_my_stones) + ['|'] + sorted(opp_stones)
        board_key = hashlib.md5(str(new_board).encode()).hexdigest()
        if board_key in memory.get('board_history', set()):
            return False
        return True

    # Find any immediate capture
    def find_capture():
        for r, c in opp_stones:
            group, libs = get_group_and_liberties(r, c)
            if len(libs) == 1:
                # This group can be captured
                capture_move = libs.pop()
                if is_legal_move(*capture_move):
                    return capture_move
        return None

    # Avoid self-atari: don't play a move that kills your group's only liberty unless it captures
    def avoid_self_atari(moves):
        safe_moves = []
        for r, c in moves:
            would_capture = False
            for nr, nc in neighbors(r, c):
                if (nr, nc) in opp_stones:
                    grp, libs = get_group_and_liberties(nr, nc)
                    if len(libs) == 1 and (r, c) in libs:
                        would_capture = True
                        break
            if would_capture:
                safe_moves.append((r, c))
                continue
            # Check if move leaves own group with at least one liberty
            new_my_stones = my_stones | {(r, c)}
            own_group = {(r, c)}
            own_liberties = set()
            for nr, nc in neighbors(r, c):
                if (nr, nc) in new_my_stones:
                    grp, libs = get_group_and_liberties(nr, nc)
                    own_group |= grp
                    own_liberties |= libs
                elif (nr, nc) not in all_stones:
                    own_liberties.add((nr, nc))
            if len(own_liberties) > 0:
                safe_moves.append((r, c))
        return safe_moves

    # Influence map heuristic for territory expansion
    def get_influence_score():
        influence = np.zeros((SIZE+1, SIZE+1), dtype=float)
        # Boost edge and center slightly
        center_weights = np.array([
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1],
            [1, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 1],
            [1, 2, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 3, 2, 1],
            [1, 2, 3, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 4, 3, 2, 1],
            [1, 2, 3, 4, 5, 6, 6, 6, 6, 6, 6, 6, 6, 6, 5, 4, 3, 2, 1],
            [1, 2, 3, 4, 5, 6, 7, 7, 7, 7, 7, 7, 7, 6, 5, 4, 3, 2, 1],
            [1, 2, 3, 4, 5, 6, 7, 8, 8, 8, 8, 7, 6, 5, 4, 3, 3, 2, 1],
            [1, 2, 3, 4, 5, 6, 7, 8, 9, 8, 7, 6, 5, 4, 3, 3, 3, 2, 1],
            [1, 2, 3, 4, 5, 6, 7, 8, 8, 8, 8, 7, 6, 5, 4, 3, 3, 2, 1],
            [1, 2, 3, 4, 5, 6, 7, 7, 7, 7, 7, 7, 7, 6, 5, 4, 3, 2, 1],
            [1, 2, 3, 4, 5, 6, 6, 6, 6, 6, 6, 6, 6, 6, 5, 4, 3, 2, 1],
            [1, 2, 3, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 4, 3, 2, 1],
            [1, 2, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 3, 2, 1],
            [1, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 1],
            [1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        ])
        influence += center_weights

        for rs, cs in my_stones:
            for dr in range(-3, 4):
                for dc in range(-3, 4):
                    nr, nc = rs + dr, cs + dc
                    if 1 <= nr <= SIZE and 1 <= nc <= SIZE:
                        dist = abs(dr) + abs(dc)
                        if dist == 0:
                            influence[nr][nc] += 4.0
                        elif dist <= 3:
                            influence[nr][nc] += 2.0 / dist
        for rs, cs in opp_stones:
            for dr in range(-3, 4):
                for dc in range(-3, 4):
                    nr, nc = rs + dr, cs + dc
                    if 1 <= nr <= SIZE and 1 <= nc <= SIZE:
                        dist = abs(dr) + abs(dc)
                        if dist == 0:
                            influence[nr][nc] -= 4.0
                        elif dist <= 3:
                            influence[nr][nc] -= 2.0 / dist
        return influence

    # --- Main policy logic ---

    # Initialize memory
    if 'board_history' not in memory:
        memory['board_history'] = set()
    if 'move_count' not in memory:
        memory['move_count'] = 0

    # Add current board state to history
    current_board = sorted(my_stones) + ['|'] + sorted(opp_stones)
    current_key = hashlib.md5(str(current_board).encode()).hexdigest()
    memory['board_history'].add(current_key)
    memory['move_count'] += 1

    # 1. First, try to capture
    capture_move = find_capture()
    if capture_move and is_legal_move(*capture_move):
        return capture_move, memory

    # 2. Generate candidate moves: empty spots near existing stones or center
    candidate_moves = set()
    # Expand nearby
    for r, c in my_stones | opp_stones:
        for nr, nc in neighbors(r, c):
            if (nr, nc) not in all_stones:
                candidate_moves.add((nr, nc))
    # Add center and star points if empty
    star_points = [(4,4), (4,10), (4,16), (10,4), (10,10), (10,16), (16,4), (16,10), (16,16)]
    for sp in star_points:
        if sp not in all_stones:
            candidate_moves.add(sp)

    # Filter legal and non-self-atari moves
    candidate_moves = [m for m in candidate_moves if is_legal_move(*m)]
    if not candidate_moves:
        return (0, 0), memory  # pass

    candidate_moves = avoid_self_atari(candidate_moves)
    if not candidate_moves:
        return (0, 0), memory  # pass

    # 3. Use influence map to score and pick best move
    influence = get_influence_score()
    best_score = -float('inf')
    best_move = None
    for r, c in candidate_moves:
        score = influence[r][c]
        if score > best_score:
            best_score = score
            best_move = (r, c)

    # Fallback
    if best_move is None:
        best_move = candidate_moves[0]

    return best_move, memory
