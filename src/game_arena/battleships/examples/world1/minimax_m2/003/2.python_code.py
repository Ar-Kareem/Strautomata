
# Precompute a list of all cells in row-major order for hunt mode
HUNT_CELLS = []
for r in range(10):
    for c in range(10):
        HUNT_CELLS.append((r, c))

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Find all hit cells
    hit_cells = []
    for r in range(10):
        for c in range(10):
            if board[r][c] == 1:
                hit_cells.append((r, c))
    
    # If no hits, use hunt mode
    if not hit_cells:
        # Find the first untargeted cell in row-major order
        for cell in HUNT_CELLS:
            r, c = cell
            if board[r][c] == 0:
                return (r, c)
    
    # If there are hits, use target mode
    # Generate set of candidate cells (unknown cells adjacent to any hit)
    candidates = set()
    for (r_hit, c_hit) in hit_cells:
        # Check four adjacent cells
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            r_candidate = r_hit + dr
            c_candidate = c_hit + dc
            # Check bounds
            if 0 <= r_candidate < 10 and 0 <= c_candidate < 10:
                if board[r_candidate][c_candidate] == 0:
                    candidates.add((r_candidate, c_candidate))
    
    # If there are candidates, choose the one with the highest score
    if candidates:
        best_score = -1
        best_candidates = []
        for (r, c) in candidates:
            # Calculate score: number of hit cells adjacent to this candidate
            score = 0
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                r_adj = r + dr
                c_adj = c + dc
                if 0 <= r_adj < 10 and 0 <= c_adj < 10:
                    if board[r_adj][c_adj] == 1:
                        score += 1
            # Update best candidates
            if score > best_score:
                best_score = score
                best_candidates = [(r, c)]
            elif score == best_score:
                best_candidates.append((r, c))
        # Choose the candidate with smallest row, then column
        best_candidates.sort()
        return best_candidates[0]
    
    # If no candidates, fall back to hunt mode
    for cell in HUNT_CELLS:
        r, c = cell
        if board[r][c] == 0:
            return (r, c)
