
def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    occupied = set(me + opponent)
    empty = []
    for r in range(1, 20):
        for c in range(1, 20):
            if (r, c) not in occupied:
                empty.append((r, c))
    if not empty:
        return ((0, 0), memory)
    
    # Early game: Play corners or center if board is mostly empty
    if len(me) + len(opponent) < 4:
        corners = [(4,4), (4,16), (16,4), (16,16)]
        for point in corners:
            if point in empty:
                return (point, memory)
        center = (10, 10)
        if center in empty:
            return (center, memory)
    
    # Check for capture opportunities
    directions = [(-1,0), (1,0), (0,-1), (0,1)]
    capture_moves = []
    for (r, c) in empty:
        capture_count = 0
        for (dr, dc) in directions:
            nr, nc = r + dr, c + dc
            if (nr, nc) in opponent:
                libs = 0
                for (dr2, dc2) in directions:
                    nr2, nc2 = nr + dr2, nc + dc2
                    if (nr2, nc2) not in occupied:
                        libs += 1
                if libs == 1:
                    capture_count += 1
        if capture_count > 0:
            capture_moves.append((capture_count, r, c))
    
    if capture_moves:
        # Prefer moves with higher captures and closer to center
        capture_moves.sort(key=lambda x: (-x[0], abs(x[1]-10) + abs(x[2]-10)))
        best = capture_moves[0][1], capture_moves[0][2]
        return (best, memory)
    
    # No captures: Expand towards stones or center
    if not me:
        return (empty[0], memory)
    
    best_move = empty[0]
    min_score = float('inf')
    for (r, c) in empty:
        min_dist = min(abs(r - mr) + abs(c - mc) for (mr, mc) in me)
        center_dist = abs(r - 10) + abs(c - 10)
        score = 0.6 * min_dist + 0.4 * center_dist
        if score < min_score:
            min_score = score
            best_move = (r, c)
    
    return (best_move, memory)
