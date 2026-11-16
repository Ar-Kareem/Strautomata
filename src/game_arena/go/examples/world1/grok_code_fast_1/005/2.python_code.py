
import random

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    # Initialize board: 1 for me, 2 for opponent, 0 for empty
    board = [[0] * 21 for _ in range(21)]
    for r, c in me:
        board[r][c] = 1
    for r, c in opponent:
        board[r][c] = 2
    
    def is_adjacent(p1, p2):
        r1, c1 = p1
        r2, c2 = p2
        return abs(r1 - r2) + abs(c1 - c2) == 1
    
    # Find all empty spots adjacent to any stone
    candidates = set()
    for stone in me + opponent:
        r, c = stone
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if abs(dr) + abs(dc) == 1:
                    nr, nc = r + dr, c + dc
                    if 1 <= nr <= 19 and 1 <= nc <= 19 and board[nr][nc] == 0:
                        candidates.add((nr, nc))
    
    if not candidates:
        return (0, 0)  # Pass if no legal adjacent spots (unlikely)
    
    # Find capturing moves: spots that are the only liberty of an opponent's stone
    capturing = set()
    for opp in opponent:
        liberties = []
        r, c = opp
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if abs(dr) + abs(dc) == 1:
                    nr, nc = r + dr, c + dc
                    if 1 <= nr <= 19 and 1 <= nc <= 19 and board[nr][nc] == 0:
                        liberties.append((nr, nc))
        if len(liberties) == 1:
            capturing.add(liberties[0])
    
    # Filter valid candidates (not suicidal: has at least one empty neighbor)
    valid_candidates = []
    for cr, cc in candidates:
        has_empty = False
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if abs(dr) + abs(dc) == 1:
                    nr, nc = cr + dr, cc + dc
                    if 1 <= nr <= 19 and 1 <= nc <= 19 and board[nr][nc] == 0:
                        has_empty = True
                        break
            if has_empty:
                break
        if has_empty:
            valid_candidates.append((cr, cc))
    
    # Prioritize capturing moves among valid ones
    possible_captures = [c for c in capturing if c in valid_candidates]
    if possible_captures:
        return random.choice(possible_captures)
    else:
        # Otherwise, random valid adjacent move
        if valid_candidates:
            return random.choice(valid_candidates)
        else:
            return (0, 0)  # Pass if none (extremely unlikely)
