
from collections import deque

# Precompute all-pairs shortest paths for 5x3 board
POSITIONS = [(r, c) for r in range(1, 6) for c in range(1, 4)]
DELTAS = [(2,1), (2,-1), (-2,1), (-2,-1), (1,2), (1,-2), (-1,2), (-1,-2)]

# Compute distances between all pairs of positions
DIST = {}
for pos in POSITIONS:
    DIST[pos] = {pos: 0}
    queue = deque([pos])
    while queue:
        r, c = queue.popleft()
        for dr, dc in DELTAS:
            nr, nc = r + dr, c + dc
            if 1 <= nr <= 5 and 1 <= nc <= 3 and (nr, nc) not in DIST[pos]:
                DIST[pos][(nr, nc)] = DIST[pos][(r, c)] + 1
                queue.append((nr, nc))

# Compute mobility (number of valid moves) for each position
MOBILITY = {}
for r, c in POSITIONS:
    MOBILITY[(r, c)] = sum(1 for dr, dc in DELTAS 
                           if 1 <= r+dr <= 5 and 1 <= c+dc <= 3)


def policy(state: list[list[object]], role: str) -> str:
    # Parse state
    knight_pos = None
    pawns = set()
    played = False
    
    for fact in state:
        if fact[0] == "cell" and fact[1] == role:
            if fact[4] == "knight":
                knight_pos = (int(fact[2]), int(fact[3]))
            elif fact[4] == "pawn":
                pawns.add((int(fact[2]), int(fact[3])))
        elif fact[0] == "played" and fact[1] == role:
            played = True
    
    # If already played this turn, tick to pass control
    if played:
        return "tick"
    
    # Get valid knight moves
    def get_moves(pos):
        r, c = pos
        return [(r+dr, c+dc) for dr, dc in DELTAS 
                if 1 <= r+dr <= 5 and 1 <= c+dc <= 3]
    
    valid_moves = get_moves(knight_pos)
    
    if not valid_moves:
        return "tick"
    
    # Score each move
    def score_move(move):
        score = 0.0
        
        # Immediate capture (highest priority)
        if move in pawns:
            score += 10000.0
        
        # Distance to remaining pawns
        remaining = pawns - {move}
        if remaining:
            total_dist = sum(DIST[move].get(p, 100) for p in remaining)
            avg_dist = total_dist / len(remaining)
            score += max(0, (20.0 - avg_dist) * 100.0)
        else:
            score += 5000.0
        
        # Mobility bonus
        score += MOBILITY[move] * 10.0
        
        return score
    
    # Find best move with tiebreaker for determinism
    best_move = max(valid_moves, key=lambda m: (score_move(m), -m[0], -m[1]))
    
    return f"move({role},{knight_pos[0]},{knight_pos[1]},{best_move[0]},{best_move[1]})"
