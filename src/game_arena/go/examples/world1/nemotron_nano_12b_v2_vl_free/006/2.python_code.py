
def policy(me, opponent):
    me_set = set(me)
    opponent_set = set(opponent)
    existing = me_set.union(opponent_set)
    
    legal_moves = []
    
    for r in range(1, 20):
        for c in range(1, 20):
            if (r, c) not in existing:
                liberties = 0
                # Check up direction
                if r > 1 and (r-1, c) not in existing:
                    liberties += 1
                # Check down direction
                if r < 19 and (r+1, c) not in existing:
                    liberties += 1
                # Check left direction
                if c > 1 and (r, c-1) not in existing:
                    liberties += 1
                # Check right direction
                if c < 19 and (r, c+1) not in existing:
                    liberties += 1
                
                if liberties >= 1:
                    legal_moves.append((r, c))
    
    if not legal_moves:
        return (0, 0)
    
    def get_position_score(r, c):
        # Define the corners first
        if (r == 1 and c == 1) or (r == 1 and c == 19) or (r == 19 and c == 1) or (r == 19 and c == 19):
            return 100
        # Then edge cells adjacent to corners
        corners = [(1, 1), (1, 19), (19, 1), (19, 19)]
        for cr, cc in corners:
            if (abs(r - cr) + abs(c - cc)) == 1:
                return 70
        # Check if on the edge but not adjacent to a corner
        if r == 1 or r == 19 or c == 1 or c == 19:
            return 30
        # Default for other cells
        return 0
    
    best_move = None
    best_score = -float('inf')
    
    for r, c in legal_moves:
        pos_sc = get_position_score(r, c)
        # Calculate the number of liberties again (already validated as >=1)
        lib_count = 0
        dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in dirs:
            nr = r + dr
            nc = c + dc
            if 1 <= nr <= 19 and 1 <= nc <= 19:
                if (nr, nc) not in existing:
                    lib_count += 1
        total_score = pos_sc + lib_count * 3  # Prioritize position with liberties
        if total_score > best_score:
            best_score = total_score
            best_move = (r, c)
    
    return best_move
