
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Configuration
    N = 10
    INITIAL_SHIPS = [5, 4, 3, 3, 2]
    
    # Helper to check bounds
    def in_bounds(r, c):
        return 0 <= r < N and 0 <= c < N

    # 1. Analyze Board State
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
        return (0, 0) # Should not happen

    # 2. Identify Sunk Ships
    # A ship is considered sunk if it forms a straight line of hits of length L,
    # and all ends are capped by misses or board boundaries.
    # We use a simple greedy approach to find lines.
    
    remaining_ships = list(INITIAL_SHIPS)
    visited_hits = set()
    sunk_cells = set()
    
    # Sort hits to process consistently
    sorted_hits = sorted(list(hits))
    
    for r, c in sorted_hits:
        if (r, c) in visited_hits:
            continue
        
        # Try to find horizontal line
        h_line = []
        curr_c = c
        while in_bounds(r, curr_c) and board[r][curr_c] == 1:
            h_line.append((r, curr_c))
            curr_c += 1
            
        # Try to find vertical line
        v_line = []
        curr_r = r
        while in_bounds(curr_r, c) and board[curr_r][c] == 1:
            v_line.append((curr_r, c))
            curr_r += 1
            
        # Check Horizontal Line
        if len(h_line) > 1:
            # Check ends
            h_min, h_max = h_line[0][1], h_line[-1][1]
            c1, c2 = h_min - 1, h_max + 1
            ends_valid = True
            # Left end
            if in_bounds(r, c1) and board[r][c1] != -1 and board[r][c1] != 1:
                ends_valid = False
            # Right end
            if in_bounds(r, c2) and board[r][c2] != -1 and board[r][c2] != 1:
                ends_valid = False
            
            # Also check if the line is "pure" (no branching)
            # Simple check: are all cells in the line strictly contiguous hits? Yes by construction.
            # Check for perpendicular hits attached to the line (intersection)
            has_branch = False
            for hr, hc in h_line:
                for dr, dc in [(-1, 0), (1, 0)]:
                    nr, nc = hr + dr, hc + dc
                    if in_bounds(nr, nc) and board[nr][nc] == 1 and (nr, nc) not in h_line:
                        has_branch = True
                        break
                if has_branch: break
            
            length = len(h_line)
            if ends_valid and not has_branch and length in remaining_ships:
                # Found sunk ship
                remaining_ships.remove(length)
                sunk_cells.update(h_line)
                visited_hits.update(h_line)

        # Check Vertical Line (similar logic)
        if len(v_line) > 1:
            v_min, v_max = v_line[0][0], v_line[-1][0]
            r1, r2 = v_min - 1, v_max + 1
            ends_valid = True
            if in_bounds(r1, c) and board[r1][c] != -1 and board[r1][c] != 1:
                ends_valid = False
            if in_bounds(r2, c) and board[r2][c] != -1 and board[r2][c] != 1:
                ends_valid = False
            
            has_branch = False
            for vr, vc in v_line:
                for dr, dc in [(0, -1), (0, 1)]:
                    nr, nc = vr + dr, vc + dc
                    if in_bounds(nr, nc) and board[nr][nc] == 1 and (nr, nc) not in v_line:
                        has_branch = True
                        break
                if has_branch: break
            
            length = len(v_line)
            if ends_valid and not has_branch and length in remaining_ships:
                remaining_ships.remove(length)
                sunk_cells.update(v_line)
                visited_hits.update(v_line)

    # Identify active hits (hits not part of confirmed sunk ships)
    active_hits = hits - sunk_cells

    # Helper to count placements covering a cell
    # Forbidden: misses and sunk_cells
    # If in Target Mode, placement MUST cover the target hit.
    def count_placements(r_target, c_target, must_cover_hit=None):
        score = 0
        # If we need to cover a specific hit, we optimize by only checking placements that include it
        if must_cover_hit:
            hr, hc = must_cover_hit
            # For each ship length
            for L in remaining_ships:
                # Check Horizontal
                # The ship must span (r_target, c_target) and (hr, hc)
                # Both must be on the line r = r_target
                if r_target == hr:
                    # range of cols for start position
                    # start col c_start satisfies: c_start <= c_target < c_start + L
                    # AND c_start <= hc < c_start + L
                    # start possibilities roughly [c_target - L + 1, c_target]
                    for c_start in range(c_target - L + 1, c_target + 1):
                        if not in_bounds(r_target, c_start): continue
                        c_end = c_start + L - 1
                        if not in_bounds(r_target, c_end): continue
                        
                        # Check coverage
                        if not (c_start <= hc <= c_end): continue
                        
                        # Check validity
                        valid = True
                        for k in range(L):
                            cell = (r_target, c_start + k)
                            if cell in misses or cell in sunk_cells:
                                valid = False
                                break
                        if valid:
                            score += 1
                
                # Check Vertical
                if c_target == hc:
                    for r_start in range(r_target - L + 1, r_target + 1):
                        if not in_bounds(r_start, c_target): continue
                        r_end = r_start + L - 1
                        if not in_bounds(r_end, c_target): continue
                        
                        if not (r_start <= hr <= r_end): continue
                        
                        valid = True
                        for k in range(L):
                            cell = (r_start + k, c_target)
                            if cell in misses or cell in sunk_cells:
                                valid = False
                                break
                        if valid:
                            score += 1
        else:
            # Hunt Mode: Count all placements covering (r_target, c_target)
            for L in remaining_ships:
                # Horizontal
                for c_start in range(c_target - L + 1, c_target + 1):
                    if not in_bounds(r_target, c_start): continue
                    c_end = c_start + L - 1
                    if not in_bounds(r_target, c_end): continue
                    
                    valid = True
                    for k in range(L):
                        cell = (r_target, c_start + k)
                        if cell in misses or cell in sunk_cells:
                            valid = False
                            break
                        # In Hunt mode, we should also avoid active hits (different ships don't overlap)
                        if cell in active_hits:
                            valid = False
                            break
                    if valid:
                        score += 1
                
                # Vertical
                for r_start in range(r_target - L + 1, r_target + 1):
                    if not in_bounds(r_start, c_target): continue
                    r_end = r_start + L - 1
                    if not in_bounds(r_end, c_target): continue
                    
                    valid = True
                    for k in range(L):
                        cell = (r_start + k, c_target)
                        if cell in misses or cell in sunk_cells:
                            valid = False
                            break
                        if cell in active_hits:
                            valid = False
                            break
                    if valid:
                        score += 1
        return score

    candidates = []
    
    # 3. Target Mode
    if active_hits:
        # Find all unknown neighbors of active hits
        target_points = set()
        for r, c in active_hits:
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if in_bounds(nr, nc) and board[nr][nc] == 0:
                    target_points.add((nr, nc))
        
        # Evaluate each target point
        # We assume the target point must connect to at least one adjacent hit
        if target_points:
            best_score = -1
            local_candidates = []
            
            for r, c in target_points:
                # Count placements for this point that cover an adjacent hit
                # We sum scores for connections to any adjacent hit?
                # Better: The score should reflect the likelihood of a ship being here.
                # Ships must pass through one of the adjacent hits.
                # We sum placements that cover (r,c) AND (adj_hit).
                
                # Find adjacent hits
                adj_hits = []
                for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nr, nc = r + dr, c + dc
                    if in_bounds(nr, nc) and board[nr][nc] == 1 and (nr, nc) in active_hits:
                        adj_hits.append((nr, nc))
                
                current_score = 0
                # For each adjacent hit, count configurations
                # Note: This might double count if a placement covers multiple hits (e.g. filling a gap)
                # But filling a gap is extremely high probability anyway, so it wins.
                
                # Optimization: To avoid double counting the same ship configuration passing through
                # multiple hits, we can just sum distinct possibilities.
                # Since N is small, simple summation is a decent heuristic.
                
                for hr, hc in adj_hits:
                    current_score += count_placements(r, c, must_cover_hit=(hr, hc))
                
                # Also consider that (r,c) could be a NEW ship touching the active hit (parallel).
                # But we usually want to sink the current one. 
                # If we only count extensions, we focus fire.
                
                if current_score > best_score:
                    best_score = current_score
                    local_candidates = [(r, c)]
                elif current_score == best_score:
                    local_candidates.append((r, c))
            
            candidates = local_candidates
            
            # If we found candidates (score > 0), proceed. 
            # If score is 0 (e.g. isolated hit that can't form a ship with remaining lengths?),
            # we might treat as Hunt mode, but usually we just pick one to verify.
            if best_score > 0:
                # Tie-breaker
                if len(candidates) > 1:
                    random.shuffle(candidates)
                    # Prefer parity
                    even = [x for x in candidates if (x[0] + x[1]) % 2 == 0]
                    if even: return even[0]
                    return candidates[0]
                return candidates[0]

    # 4. Hunt Mode
    # If no active hits, or target logic failed (score 0), use probability map on all unknowns.
    
    # Optimization: If target_points were found but score was 0, we should still probably shoot them?
    # No, if score is 0, it means no remaining ship can connect the hit. 
    # This implies the hit is invalid or ships are accounted for. Treat as Hunt.
    
    best_score = -1
    hunt_candidates = []
    
    # Iterate all unknown cells
    # To speed up, we can skip parity if needed, but 10x10 is fast enough.
    
    for r in range(N):
        for c in range(N):
            if board[r][c] != 0:
                continue
            
            # Calculate density
            score = count_placements(r, c, must_cover_hit=None)
            
            if score > best_score:
                best_score = score
                hunt_candidates = [(r, c)]
            elif score == best_score:
                hunt_candidates.append((r, c))

    if not hunt_candidates:
        # Fallback: pick any 0 (should not happen if logic is correct)
        for r in range(N):
            for c in range(N):
                if board[r][c] == 0:
                    return (r, c)
        return (0, 0)

    # Tie-breaking: Checkerboard parity
    # Smallest ship is 2, so parity is efficient
    even_candidates = [x for x in hunt_candidates if (x[0] + x[1]) % 2 == 0]
    odd_candidates = [x for x in hunt_candidates if (x[0] + x[1]) % 2 == 1]
    
    # Prefer even (standard checkerboard)
    if even_candidates:
        return random.choice(even_candidates)
    
    return random.choice(odd_candidates)
