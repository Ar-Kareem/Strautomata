
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # Generate all legal moves
    legal_moves = []
    for row in range(5):
        for col in range(5):
            if horizontal[row, col] == 0:
                legal_moves.append((row, col, 'H'))
            if vertical[row, col] == 0:
                legal_moves.append((row, col, 'V'))
    
    def count_captures(move):
        r, c, dir = move
        captures = 0
        if dir == 'H':
            # Check box above (r-1, c)
            if r > 0 and capture[r-1, c] == 0:
                if (horizontal[r-1, c] != 0 and
                    vertical[r-1, c] != 0 and
                    vertical[r-1, c+1] != 0):
                    captures += 1
            # Check box below (r, c)
            if r < 4 and capture[r, c] == 0:
                if (horizontal[r+1, c] != 0 and
                    vertical[r, c] != 0 and
                    vertical[r, c+1] != 0):
                    captures += 1
        else:
            # Check box left (r, c-1)
            if c > 0 and capture[r, c-1] == 0:
                if (horizontal[r, c-1] != 0 and
                    horizontal[r+1, c-1] != 0 and
                    vertical[r, c-1] != 0):
                    captures += 1
            # Check box right (r, c)
            if c < 4 and capture[r, c] == 0:
                if (horizontal[r, c] != 0 and
                    horizontal[r+1, c] != 0 and
                    vertical[r, c+1] != 0):
                    captures += 1
        return captures
    
    def danger_score(move):
        score = 0
        r, c, dir = move
        if dir == 'H':
            # Box above (r-1, c)
            if r > 0 and capture[r-1, c] == 0:
                filled = (horizontal[r-1, c] != 0 +
                          vertical[r-1, c] != 0 +
                          vertical[r-1, c+1] != 0)
                if filled + 1 == 3:
                    score += 1
            # Box below (r, c)
            if r < 4 and capture[r, c] == 0:
                filled = (horizontal[r+1, c] != 0 +
                          vertical[r, c] != 0 +
                          vertical[r, c+1] != 0)
                if filled + 1 == 3:
                    score += 1
        else:
            # Box left (r, c-1)
            if c > 0 and capture[r, c-1] == 0:
                filled = (horizontal[r, c-1] != 0 +
                          horizontal[r+1, c-1] != 0 +
                          vertical[r, c-1] != 0)
                if filled + 1 == 3:
                    score += 1
            # Box right (r, c)
            if c < 4 and capture[r, c] == 0:
                filled = (horizontal[r, c] != 0 +
                          horizontal[r+1, c] != 0 +
                          vertical[r, c+1] != 0)
                if filled + 1 == 3:
                    score += 1
        return score
    
    # Check for capturing moves
    capture_moves = []
    for move in legal_moves:
        cnt = count_captures(move)
        if cnt > 0:
            capture_moves.append((move, cnt))
    
    if capture_moves:
        # Find max captures
        max_capt = max(c[1] for c in capture_moves)
        best_candidates = [c for c in capture_moves if c[1] == max_capt]
        # Select move with minimal danger
        min_danger = float('inf')
        best_move = None
        for cand in best_candidates:
            d = danger_score(cand[0])
            if d < min_danger:
                min_danger = d
                best_move = cand[0]
        r, c, d = best_move
        return f"{r},{c},{d}"
    
    # No captures; select safest move
    min_danger = float('inf')
    safe_moves = []
    for move in legal_moves:
        d = danger_score(move)
        if d < min_danger:
            min_danger = d
            safe_moves = [move]
        elif d == min_danger:
            safe_moves.append(move)
    # Select first move (arbitrary choice among equally safe moves)
    r, c, d = safe_moves[0]
    return f"{r},{c},{d}"
