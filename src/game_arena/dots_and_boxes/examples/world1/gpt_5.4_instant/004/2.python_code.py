
import numpy as np
from collections import deque

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    N = 4  # 4x4 boxes, arrays are 5x5

    def box_sides_filled(r, c, h=None, v=None):
        if h is None:
            h = horizontal
        if v is None:
            v = vertical
        return int(h[r, c] != 0) + int(h[r + 1, c] != 0) + int(v[r, c] != 0) + int(v[r, c + 1] != 0)

    def adjacent_boxes(move):
        r, c, d = move
        boxes = []
        if d == 'H':
            if r > 0:
                boxes.append((r - 1, c))
            if r < N:
                boxes.append((r, c))
        else:  # 'V'
            if c > 0:
                boxes.append((r, c - 1))
            if c < N:
                boxes.append((r, c))
        return [(br, bc) for br, bc in boxes if 0 <= br < N and 0 <= bc < N]

    def apply_move_temp(move):
        r, c, d = move
        h = horizontal.copy()
        v = vertical.copy()
        cap = capture.copy()
        if d == 'H':
            h[r, c] = 1
        else:
            v[r, c] = 1
        gained = 0
        for br, bc in adjacent_boxes(move):
            if cap[br, bc] == 0 and box_sides_filled(br, bc, h, v) == 4:
                cap[br, bc] = 1
                gained += 1
        return h, v, cap, gained

    def legal_moves():
        moves = []
        for r in range(5):
            for c in range(4):
                if horizontal[r, c] == 0:
                    moves.append((r, c, 'H'))
        for r in range(4):
            for c in range(5):
                if vertical[r, c] == 0:
                    moves.append((r, c, 'V'))
        return moves

    def move_creates_threes(move):
        # Number of adjacent uncaptured boxes that become exactly 3-sided after this move
        h, v, cap, gained = apply_move_temp(move)
        cnt = 0
        for br, bc in adjacent_boxes(move):
            if cap[br, bc] == 0 and box_sides_filled(br, bc, h, v) == 3:
                cnt += 1
        return cnt

    def move_creates_twos(move):
        h, v, cap, gained = apply_move_temp(move)
        cnt = 0
        for br, bc in adjacent_boxes(move):
            if cap[br, bc] == 0 and box_sides_filled(br, bc, h, v) == 2:
                cnt += 1
        return cnt

    def box_missing_edges(br, bc, h, v, cap):
        if cap[br, bc] != 0:
            return []
        missing = []
        if h[br, bc] == 0:
            missing.append((br, bc, 'H'))
        if h[br + 1, bc] == 0:
            missing.append((br + 1, bc, 'H'))
        if v[br, bc] == 0:
            missing.append((br, bc, 'V'))
        if v[br, bc + 1] == 0:
            missing.append((br, bc + 1, 'V'))
        return missing

    def chain_graph_after(move):
        # Build graph of currently 2-sided boxes after move, where an edge exists if
        # boxes share a missing edge; this approximates sacrifice chain sizes.
        h, v, cap, _ = apply_move_temp(move)
        candidates = []
        for br in range(N):
            for bc in range(N):
                if cap[br, bc] == 0 and box_sides_filled(br, bc, h, v) == 2:
                    candidates.append((br, bc))

        cand_set = set(candidates)
        graph = {b: [] for b in candidates}

        for br, bc in candidates:
            miss = set(box_missing_edges(br, bc, h, v, cap))
            for nbr in [(br - 1, bc), (br + 1, bc), (br, bc - 1), (br, bc + 1)]:
                if nbr in cand_set:
                    nmiss = set(box_missing_edges(nbr[0], nbr[1], h, v, cap))
                    if miss & nmiss:
                        graph[(br, bc)].append(nbr)

        comps = []
        seen = set()
        for b in candidates:
            if b in seen:
                continue
            q = deque([b])
            seen.add(b)
            size = 0
            while q:
                x = q.popleft()
                size += 1
                for y in graph[x]:
                    if y not in seen:
                        seen.add(y)
                        q.append(y)
            comps.append(size)
        comps.sort()
        return comps

    def sacrifice_cost(move):
        # Lower is better.
        # Unsafe moves create 3-sided boxes. Estimate how much chain value is handed over.
        threes = move_creates_threes(move)
        if threes == 0:
            return -1000  # safe move
        comps = chain_graph_after(move)
        # Prefer opening smaller structures; combine immediate danger with component sizes.
        # If graph approximation is weak, immediate threes still dominates.
        score = threes * 100
        if comps:
            score += max(comps) * 10 + sum(comps)
        # Slight preference for edge/corner openings over center
        r, c, d = move
        central_penalty = 0
        if d == 'H':
            if 1 <= r <= 3 and 1 <= c <= 2:
                central_penalty = 1
        else:
            if 1 <= r <= 2 and 1 <= c <= 3:
                central_penalty = 1
        score += central_penalty
        return score

    moves = legal_moves()
    if not moves:
        return "0,0,H"

    # 1. Immediate scoring moves
    scoring = []
    for mv in moves:
        _, _, _, gained = apply_move_temp(mv)
        if gained > 0:
            scoring.append((gained, mv))
    if scoring:
        scoring.sort(key=lambda x: (-x[0], x[1][0], x[1][1], x[1][2]))
        r, c, d = scoring[0][1]
        return f"{r},{c},{d}"

    # 2. Safe moves: do not create 3-sided boxes
    safe = [mv for mv in moves if move_creates_threes(mv) == 0]
    if safe:
        # Minimize creation of 2-sided boxes, then prefer boundary moves.
        def safe_key(mv):
            twos = move_creates_twos(mv)
            r, c, d = mv
            # boundary preference
            if d == 'H':
                boundary = int(r == 0 or r == 4)
            else:
                boundary = int(c == 0 or c == 4)
            center_dist = abs(r - 2) + abs(c - 2)
            return (twos, -boundary, -center_dist, r, c, d)
        best = min(safe, key=safe_key)
        r, c, d = best
        return f"{r},{c},{d}"

    # 3. All moves unsafe: minimize sacrifice
    best = min(moves, key=lambda mv: (sacrifice_cost(mv), mv[0], mv[1], mv[2]))
    r, c, d = best
    return f"{r},{c},{d}"
