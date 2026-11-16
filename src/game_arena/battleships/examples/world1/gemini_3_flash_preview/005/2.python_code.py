
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Battleship AI targeting policy.
    0 = unknown, -1 = miss, 1 = hit.
    """
    size = 10
    hits = []
    unknowns = []
    
    for r in range(size):
        for c in range(size):
            if board[r][c] == 1:
                hits.append((r, c))
            elif board[r][c] == 0:
                unknowns.append((r, c))

    # Target Mode: If there are hits, try to sink the ship
    if hits:
        target_candidates = {} # (r, c) -> priority score
        
        for r, c in hits:
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < size and 0 <= nc < size and board[nr][nc] == 0:
                    # Check if this direction aligns with other hits (line discovery)
                    priority = 1
                    # Look further in the opposite direction
                    if 0 <= r - dr < size and 0 <= c - dc < size and board[r - dr][c - dc] == 1:
                        priority = 2 # Higher priority for maintaining a line
                    
                    target_candidates[(nr, nc)] = max(target_candidates.get((nr, nc), 0), priority)
        
        if target_candidates:
            # Pick the highest priority; tie-break randomly
            max_p = max(target_candidates.values())
            best_targets = [k for k, v in target_candidates.items() if v == max_p]
            return random.choice(best_targets)

    # Hunt Mode: Use parity and potential ship fits
    # Parity: Target cells where (r + c) % 2 == 0
    # Also weight candidates by how many 2-length segments can fit (simplification of PDF)
    best_cell = None
    max_weight = -1
    
    # Shuffle unknowns to add variety
    random.shuffle(unknowns)
    
    for r, c in unknowns:
        weight = 0
        # Check horizontal/vertical space
        for dr, dc in [(0, 1), (1, 0)]:
            # Look at a window of 3 centered or starting at r, c to see if a ship could fit
            # This is a simple heuristic for "density"
            for offset in range(-2, 1):
                can_fit = True
                for i in range(3):
                    tr, tc = r + dr * (offset + i), c + dc * (offset + i)
                    if not (0 <= tr < size and 0 <= tc < size and board[tr][tc] != -1):
                        can_fit = False
                        break
                if can_fit:
                    weight += 1
        
        # Checkerboard parity (prefers r+c even)
        parity_bonus = 1 if (r + c) % 2 == 0 else 0
        total_score = weight + parity_bonus
        
        if total_score > max_weight:
            max_weight = total_score
            best_cell = (r, c)

    return best_cell if best_cell else random.choice(unknowns)

