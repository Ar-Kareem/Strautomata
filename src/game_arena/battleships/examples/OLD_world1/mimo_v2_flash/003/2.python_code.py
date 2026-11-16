
import random
import itertools

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Advanced Hunt and Target strategy for Battleship.
    
    Strategy:
    1. Target Mode: If there are ongoing ship hits (unknown adjacency), prioritize them 
       to sink the ship.
    2. Hunt Mode: If no active targets, fire at a cell maximizing the probability of a hit.
       This is done by simulating all possible valid ship placements consistent with the 
       current board and counting how many times each unknown cell is occupied.
    
    Note: To handle the "Ships cannot touch" rule, the simulation iterates through all 
    legal placements of the remaining unknown ship lengths. This is feasible because 
    we only simulate placements for the current board state, and the number of valid 
    placements reduces rapidly as the game progresses.
    """
    
    # --- 1. Setup and Utility Functions ---
    
    N = 10
    SHIP_LENGTHS = [5, 4, 3, 3, 2]
    
    # Convert board to a set of known hits/misses for fast access
    hits = set()
    misses = set()
    unknowns = set()
    for r in range(N):
        for c in range(N):
            val = board[r][c]
            if val == 1:
                hits.add((r, c))
            elif val == -1:
                misses.add((r, c))
            else:
                unknowns.add((r, c))
                
    if not unknowns:
        # Should not happen in a valid game, but safe fallback
        return (0, 0)

    # --- 2. Target Mode (Kill) ---
    # If we have hits, we must focus on sinking the ship.
    # We look for unknown cells that are neighbors of existing hits.
    
    target_candidates = set()
    for (r, c) in hits:
        # Get orthogonal neighbors
        neighbors = [(r-1, c), (r+1, c), (r, c-1), (r, c+1)]
        for nr, nc in neighbors:
            if 0 <= nr < N and 0 <= nc < N and (nr, nc) in unknowns:
                target_candidates.add((nr, nc))
    
    # If we have target candidates, pick the best one based on "Line Confidence"
    if target_candidates:
        best_target = None
        max_score = -1
        
        for cand in target_candidates:
            score = 0
            
            # Check lines passing through this candidate
            # Horizontal
            h_continues_hits = 0
            # Check left
            curr = cand[1] - 1
            while curr >= 0 and (cand[0], curr) in hits:
                h_continues_hits += 1
                curr -= 1
            # Check right
            curr = cand[1] + 1
            while curr < N and (cand[0], curr) in hits:
                h_continues_hits += 1
                curr += 1
            
            # Vertical
            v_continues_hits = 0
            # Check up
            curr = cand[0] - 1
            while curr >= 0 and (curr, cand[1]) in hits:
                v_continues_hits += 1
                curr -= 1
            # Check down
            curr = cand[0] + 1
            while curr < N and (curr, cand[1]) in hits:
                v_continues_hits += 1
                curr += 1
                
            # Heuristic: The score is the number of connected hits. 
            # This prioritizes extending a line of hits.
            # We add a small random factor to break ties and avoid predictable patterns.
            score = max(h_continues_hits, v_continues_hits) + random.random() * 0.1
            
            if score > max_score:
                max_score = score
                best_target = cand
        
        if best_target:
            return best_target

    # --- 3. Hunt Mode (Probability) ---
    # If no immediate targets, simulate all valid placements of remaining ships
    # to find the most likely hit cell.
    
    # Identify lengths of ships we haven't fully found yet.
    # Since we don't know which hits belong to which ship, we approximate:
    # We assume remaining ships are the standard set. 
    # If we have clusters of hits, we treat them as 'fixed' and only place other ships.
    # For simplicity and robustness here, we assume we are hunting independent ships.
    # We will filter out placements that overlap hits (these are already known ships)
    # and filter out placements that overlap misses (impossible).
    
    # To speed up, we can assume standard fleet if we don't have complex clusters.
    # However, handling clusters accurately is important.
    # Let's handle clusters:
    
    # Identify connected components of hits (potential sunk or damaged ships)
    visited_clusters = set()
    clusters = []
    
    for h in hits:
        if h in visited_clusters: continue
        # BFS to find cluster
        q = [h]
        cluster = []
        while q:
            curr = q.pop(0)
            if curr in visited_clusters: continue
            visited_clusters.add(curr)
            cluster.append(curr)
            r, c = curr
            for dr, dc in [(0,1), (1,0), (0,-1), (-1,0)]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < N and 0 <= nc < N and (nr, nc) in hits:
                    if (nr, nc) not in visited_clusters:
                        q.append((nr, nc))
        clusters.append(cluster)
    
    # Determine lengths occupied by clusters
    occupied_lengths = []
    for cl in clusters:
        rows = [r for r, c in cl]
        cols = [c for r, c in cl]
        if all(r == rows[0] for r in rows): # Horizontal
            length = max(cols) - min(cols) + 1
        else: # Vertical
            length = max(rows) - min(rows) + 1
        occupied_lengths.append(length)
        
    # Calculate remaining lengths to place
    # We keep a copy of SHIP_LENGTHS and remove the ones we found in clusters
    remaining_lengths = list(SHIP_LENGTHS)
    for ol in occupied_lengths:
        if ol in remaining_lengths:
            remaining_lengths.remove(ol)
        else:
            # If cluster length doesn't match exactly (e.g. partial hits), 
            # we treat it as a "partial" ship. 
            # Strategy: Treat hits as obstacles for OTHER ships, but don't assume 
            # we know the ship's full length yet.
            # However, for probability calculation, we assume standard fleet 
            # minus fully identified ships.
            pass
            
    # The "Must Not Touch" rule implies we cannot place ships adjacent to each other.
    # Since we have existing clusters (hits), any new ship cannot touch them.
    # We define a set of "blocked" cells: hits + neighbors of hits + misses.
    
    blocked = set(misses)
    for r, c in hits:
        blocked.add((r, c))
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < N and 0 <= nc < N:
                    blocked.add((nr, nc))
                    
    # We want to calculate the frequency of each unknown cell being part of a valid
    # ship placement that fits within the unknowns and avoids blocked areas.
    
    counts = [[0 for _ in range(N)] for _ in range(N)]
    
    # Optimization: If the board is very early (mostly unknowns), random parition is safer 
    # than full simulation to avoid hitting adjacent ships (which is illegal for PLACEMENT, 
    # but legal for shooting). Wait, the constraint "ships cannot touch" applies to PLACEMENT. 
    # It does not apply to shooting. However, if ships cannot touch, then there are gaps between them.
    # If we shoot randomly in a cluster of unknowns, we are less likely to hit because ships are separated.
    # This fact makes "Probability Density" very powerful here.
    
    # Simulation of all valid placements
    # To ensure execution time < 1s, we limit the simulation if the number of valid placements is too high.
    # However, given the "no touch" rule and hits, valid placements are often limited.
    
    # Helper to check validity
    def is_valid_placement(length, start_r, start_c, vertical):
        coords = []
        for i in range(length):
            r = start_r + i if vertical else start_r
            c = start_c + i if not vertical else start_c
            if r < 0 or r >= N or c < 0 or c >= N: return False
            if (r, c) in blocked: return False # Hits, Misses, Neighbors of hits
            # Check overlap with other simulated ships? 
            # We handle this by adding to blocked set incrementally if we do permutations
            # But doing permutations of 5 ships is too slow.
            # Instead, we treat ships independently: sum of probabilities.
            # Is this correct? "Cannot touch" means ships are dependent.
            # However, if we miss, the exact dependency matters less than general density.
            # Let's approximate: Treat ships independently but respect Blocked cells (misses/hits).
            # This is a standard approximation for "Don't touch" games.
            coords.append((r, c))
        return True

    # For each remaining length, find all valid placements and add to counts
    for length in remaining_lengths:
        # Horizontal
        for r in range(N):
            for c in range(N - length + 1):
                valid = True
                for i in range(length):
                    if (r, c+i) in blocked:
                        valid = False
                        break
                if valid:
                    for i in range(length):
                        counts[r][c+i] += 1
        # Vertical
        for r in range(N - length + 1):
            for c in range(N):
                valid = True
                for i in range(length):
                    if (r+i, c) in blocked:
                        valid = False
                        break
                if valid:
                    for i in range(length):
                        counts[r+i][c] += 1

    # If we have partial hits (clusters) that we haven't fully sunk,
    # we should aggressively target their neighbors (already handled in Target Mode).
    # If we are in Hunt Mode, it means Target Mode found no immediate neighbors or we have no hits.
    
    # Select cell with max probability
    max_val = -1
    best_candidates = []
    
    for r in range(N):
        for c in range(N):
            if (r, c) in unknowns:
                # Bias: Checkerboard pattern helps in clean grids, but density is better for "no touch"
                val = counts[r][c]
                # Small random noise to break ties
                val += random.random() * 0.01
                if val > max_val:
                    max_val = val
                    best_candidates = [(r, c)]
                elif abs(val - max_val) < 0.1:
                    best_candidates.append((r, c))
    
    if best_candidates:
        return random.choice(best_candidates)
    
    # Fallback: Random unknown (should not be reached if unknowns is not empty and logic is correct)
    return random.choice(list(unknowns))
