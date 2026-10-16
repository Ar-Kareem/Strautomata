
import time
from collections import deque
import numpy as np

DIRS = [
    (-1, 0), (1, 0), (0, -1), (0, 1),
    (-1, -1), (-1, 1), (1, -1), (1, 1)
]

def in_bounds(r, c):
    return 0 <= r < 6 and 0 <= c < 6

def get_queen_moves(b, r, c):
    moves = []
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        while in_bounds(nr, nc) and b[nr, nc] == 0:
            moves.append((nr, nc))
            nr += dr
            nc += dc
    return moves

def count_queen_moves(b, r, c):
    cnt = 0
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        while in_bounds(nr, nc) and b[nr, nc] == 0:
            cnt += 1
            nr += dr
            nc += dc
    return cnt

def get_total_mobility(b, player_val):
    cnt = 0
    for r in range(6):
        for c in range(6):
            if b[r, c] == player_val:
                cnt += count_queen_moves(b, r, c)
    return cnt

def compute_queen_distances(b, player_val):
    dist = [[99] * 6 for _ in range(6)]
    queue = deque()
    
    for r in range(6):
        for c in range(6):
            if b[r, c] == player_val:
                for nr, nc in get_queen_moves(b, r, c):
                    if dist[nr][nc] > 1:
                        dist[nr][nc] = 1
                        queue.append((nr, nc, 1))
                        
    while queue:
        r, c, d = queue.popleft()
        if d >= 3:
            continue
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while in_bounds(nr, nc) and b[nr, nc] == 0:
                if dist[nr][nc] > d + 1:
                    dist[nr][nc] = d + 1
                    queue.append((nr, nc, d + 1))
                nr += dr
                nc += dc
    return dist

def evaluate_territory(b):
    d1 = compute_queen_distances(b, 1)
    d2 = compute_queen_distances(b, 2)
    score = 0.0
    for r in range(6):
        for c in range(6):
            if b[r, c] == 0:
                dist1 = d1[r][c]
                dist2 = d2[r][c]
                if dist1 < dist2:
                    score += 1.0 + (dist2 - dist1) * 0.1
                elif dist2 < dist1:
                    score -= 1.0 + (dist1 - dist2) * 0.1
    return score

def policy(board) -> str:
    start_time = time.time()
    time_limit = 0.88  # safety margin for 1.0 second limit
    
    # Ensure board is a standard 6x6 numpy array
    b = np.array(board, dtype=int)
    
    my_amazons = []
    opp_amazons = []
    for r in range(6):
        for c in range(6):
            if b[r, c] == 1:
                my_amazons.append((r, c))
            elif b[r, c] == 2:
                opp_amazons.append((r, c))

    # Generate all legal moves for player 1
    legal_moves = []
    for fr, fc in my_amazons:
        to_destinations = get_queen_moves(b, fr, fc)
        for tr, tc in to_destinations:
            # Temporarily move amazon
            b[fr, fc] = 0
            b[tr, tc] = 1
            
            arrow_destinations = get_queen_moves(b, tr, tc)
            for ar, ac in arrow_destinations:
                legal_moves.append(((fr, fc), (tr, tc), (ar, ac)))
            
            # Undo move
            b[tr, tc] = 0
            b[fr, fc] = 1

    if not legal_moves:
        return "0,0:0,0:0,0"

    # Fast evaluation pass
    scored_moves = []
    for move in legal_moves:
        (fr, fc), (tr, tc), (ar, ac) = move
        b[fr, fc] = 0
        b[tr, tc] = 1
        b[ar, ac] = -1
        
        # Immediate opponent mobility
        opp_mob = sum(count_queen_moves(b, opr, opc) for opr, opc in opp_amazons)
        if opp_mob == 0:
            # Immediate trap & win!
            b[ar, ac] = 0
            b[tr, tc] = 0
            b[fr, fc] = 1
            return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"
        
        my_mob = sum(count_queen_moves(b, r, c) for r, c in my_amazons if (r, c) != (fr, fc))
        my_mob += count_queen_moves(b, tr, tc)
        
        fast_score = my_mob - 1.6 * opp_mob
        scored_moves.append((fast_score, move))
        
        b[ar, ac] = 0
        b[tr, tc] = 0
        b[fr, fc] = 1

    # Sort descending by fast score
    scored_moves.sort(key=lambda x: x[0], reverse=True)

    # Perform deeper evaluation on top candidates within time budget
    candidates_to_eval = min(len(scored_moves), 25)
    best_move = scored_moves[0][1]
    best_val = -1e9

    for i in range(candidates_to_eval):
        if time.time() - start_time > time_limit:
            break
            
        fast_score, move = scored_moves[i]
        (fr, fc), (tr, tc), (ar, ac) = move
        
        b[fr, fc] = 0
        b[tr, tc] = 1
        b[ar, ac] = -1
        
        territory = evaluate_territory(b)
        
        # Adversarial 1-ply mobility response
        # Find the best move opponent could make in terms of their own mobility
        opp_best_mob = 0
        for opr, opc in opp_amazons:
            for otr, otc in get_queen_moves(b, opr, opc):
                # If opponent moves here, count their moves
                b[opr, opc] = 0
                b[otr, otc] = 2
                mob_from_new = count_queen_moves(b, otr, otc)
                if mob_from_new > opp_best_mob:
                    opp_best_mob = mob_from_new
                b[otr, otc] = 0
                b[opr, opc] = 2

        b[ar, ac] = 0
        b[tr, tc] = 0
        b[fr, fc] = 1
        
        total_eval = fast_score + 1.2 * territory - 0.8 * opp_best_mob
        if total_eval > best_val:
            best_val = total_eval
            best_move = move

    (fr, fc), (tr, tc), (ar, ac) = best_move
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"
