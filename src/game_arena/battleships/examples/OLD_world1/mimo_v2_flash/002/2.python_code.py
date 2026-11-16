
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    A battleship targeting policy that simulates likely opponent configurations
    based on standard ship constraints (5,4,3,3,2) and prioritizes the most
    probable locations of remaining unknown ship cells.
    
    Strategy:
    1. Identify all unknown cells and existing hits.
    2. Generate a set of candidate ships (horizontal and vertical) that:
       - Fit entirely within the unknown/known-hit area.
       - Do not cover any known miss (-1).
       - Are consistent with the current hits (if any).
    3. If we have unsunk hits (connected components of '1's), filter candidates 
       to only those that cover at least one cell of the component, enforcing
       that the component must be part of a valid ship placement.
    4. Compute a heat map counting how many candidate placements cover each cell.
    5. If no candidates exist (which might happen in edge cases or late game),
       fall back to a high-probability parity checkerboard pattern.
    6. Select the unknown cell with the highest heat count. Break ties randomly.
    """

    N = 10
    SHIP_SIZES = [5, 4, 3, 3, 2]

    # 1. Parse board state
    unknown_cells = set()
    hits = set()
    misses = set()
    for r in range(N):
        for c in range(N):
            val = board[r][c]
            if val == 0:
                unknown_cells.add((r, c))
            elif val == 1:
                hits.add((r, c))
            elif val == -1:
                misses.add((r, c))

    # 2. Helper: Find connected components of hits
    # These must be subsets of a single ship.
    def get_hit_components(hits_set):
        comps = []
        visited = set()
        for r, c in hits_set:
            if (r, c) in visited:
                continue
            # Start BFS/DFS
            stack = [(r, c)]
            comp = []
            while stack:
                cr, cc = stack.pop()
                if (cr, cc) in visited:
                    continue
                visited.add((cr, cc))
                comp.append((cr, cc))
                # Check 4 neighbors
                for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < N and 0 <= nc < N and (nr, nc) in hits_set:
                        if (nr, nc) not in visited:
                            stack.append((nr, nc))
            comps.append(comp)
        return comps

    hit_components = get_hit_components(hits)

    # 3. Determine constraint ship sizes
    # We need to assign lengths to components. 
    # Since components must be part of a single ship, their length cannot exceed
    # the size of any remaining ship. We assume the shortest valid ship is assigned
    # (to be conservative with space usage).
    
    # We need to find valid placements for the remaining ships.
    # We have SHIP_SIZES initially.
    # We subtract lengths of "sunk" components (components that match a ship size exactly).
    # For components that are strictly smaller than any available ship size, they are "partial".
    # For the simulation, we will treat "partial" components as fixed constraints for ships
    # of specific lengths (the minimum remaining length that can cover them).
    
    # To be robust, we'll try to match components to ship sizes.
    # Let's sort available sizes descending.
    available_sizes = sorted(SHIP_SIZES, reverse=True)
    
    # Track which components are "resolved" (fully sunk)
    resolved_components = []
    unresolved_components = []
    
    # Simple assignment logic:
    # A component is resolved if its length matches one of the available sizes exactly.
    # A component is unresolved if its length is smaller than any available size.
    # This is a simplification. A better approach is to iterate possible assignments,
    # but for a heuristic policy, checking constraints for all possible remaining lengths is usually sufficient.
    # However, to strictly follow "sunk" logic:
    # If a component length equals a specific ship size, that ship is sunk and removed from constraints.
    # If a component length is smaller, it must be part of a larger ship.
    
    # Let's refine: We don't need to guess *which* ship it is perfectly.
    # We need to generate candidates for the *remaining* ships.
    # If a component of length 2 exists, and we have sizes [5, 4, 3, 3, 2], we must consider
    # that it could be the size 2 ship (sunk) OR part of a 3, 4, or 5.
    # To be efficient, we will NOT remove sunk ships. We will simply enforce that
    # any candidate ship must either:
    # 1. Be a superset of a component (if component size < ship size).
    # 2. Match the component exactly (if component size == ship size).
    # (If component size > ship size, invalid, so component doesn't constrain this ship size).
    
    # We will iterate through available sizes. 
    # Note: If a size 5 ship is sunk (length 5 component), we should remove 5 from available_sizes.
    # But since we don't know if a length 5 component is the 5-ship or a 3+2 overlap (impossible), 
    # or just a partial 5-ship, let's stick to the "Candidate Generation" method.
    
    # Refinement: Use the "Constraint" method.
    # We generate candidates for the ships based on the board state.
    # We will generate candidates for lengths that are needed.
    
    needed_lengths = []
    
    # Identify components and what lengths they demand.
    # We must be careful not to double count.
    # We will use a simple logic: 
    # 1. Identify all components.
    # 2. For each component, the required length must be >= component size.
    # 3. We have a set of available lengths.
    # 4. We need to cover the components with these lengths.
    
    # Since we are simulating, we can just try to fit the remaining ships into the board
    # respecting the hits as "must cover" nodes.
    
    # Let's create a list of "Must Cover" sets. Each set represents a component.
    # We need to assign a ship to each component.
    # But we don't know which ship goes to which component.
    
    # Simplified Approach for this Policy:
    # We will generate candidates for all available lengths (original set minus lengths of fully sunk ships).
    # "Fully sunk" means a component length matches a ship length exactly.
    # We will remove that length and that component from consideration for future placements.
    
    # Step A: Remove sunk ships and mark their cells as satisfied.
    active_components = hit_components[:]
    active_sizes = SHIP_SIZES[:] # Copy
    
    # Sort components by length desc
    active_components.sort(key=len, reverse=True)
    
    # We try to match largest components to largest ships to "sink" them.
    # This reduces the number of constraints for simulation.
    components_satisfied_by_fixed_ships = set() # Indices of active_components
    sizes_taken = set()
    
    # Simple greedy matching for sunk detection
    comp_indices_to_remove = []
    size_indices_to_remove = []
    
    # Map: component -> required_min_size
    # If we can match a component exactly to a size, we do it.
    # Iterate sizes descending.
    for size in sorted(active_sizes, reverse=True):
        for i, comp in enumerate(active_components):
            if i in components_satisfied_by_fixed_ships: continue
            if len(comp) == size:
                components_satisfied_by_fixed_ships.add(i)
                sizes_taken.add(size)
                break
            # If component is larger than size, it cannot be satisfied by this size.
            # If component is smaller, it might be part of this size, but we prefer exact matches for "sunk" logic.
            # However, if we have a hit component of size 1, and we have a size 2 ship, it's not sunk.
            # So we only mark as sunk on exact match.
    
    # Remove taken sizes from active_sizes for simulation of remaining ships
    remaining_sizes = [s for s in active_sizes if s not in sizes_taken]
    
    # Now, for simulation:
    # We need to place the `remaining_sizes` ships.
    # They MUST cover the components that are NOT in `components_satisfied_by_fixed_ships`.
    # And they MUST NOT cover cells in `misses`.
    # They CAN cover `unknown_cells` and `hits` (but hits not in satisfied components).
    
    # Collect all hits that are NOT part of sunk ships.
    # These are the "active hits" that must be covered by our simulation candidates.
    active_hits = set()
    for i, comp in enumerate(active_components):
        if i not in components_satisfied_by_fixed_ships:
            active_hits.update(comp)
            
    # If there are no remaining ships, we are done (should not happen unless board is full), 
    # but policy must return a move.
    if not remaining_sizes:
        # Fallback to random unknown
        if unknown_cells:
            return random.choice(list(unknown_cells))
        return (0, 0) # Should not happen in valid game

    # 4. Generate Candidates
    # We generate candidates for the `remaining_sizes`.
    # We need to generate combinations of ships that cover the active hits.
    # Since generating all combinations of ships is expensive, we will use a heuristic:
    # For each remaining ship size, generate ALL valid placements (ignoring overlap with other ships for now),
    # but strictly enforcing:
    # 1. Bounds.
    # 2. No overlap with misses.
    # 3. Must overlap with active_hits (if active_hits is not empty).
    #    *Correction*: If active_hits is empty, we are in search mode (no open hits).
    
    # To make this computationally feasible in 1 second:
    # We will calculate a heat map.
    # We will iterate over each remaining ship size.
    # For each size, we generate all possible placements (O(100 * 10 * 2) = 2000 checks per size).
    # We filter these placements based on the constraints.
    # We count how many valid placements cover a given cell.
    # The cell with the highest count is the most likely to contain a ship.
    
    # But wait, there are multiple ships. The "Must Cover" logic is crucial.
    # We need to ensure that a valid set of ships exists covering the active hits.
    # This is a "Constraint Satisfaction" problem.
    
    # Optimization:
    # We will only consider "Partial Constraints". 
    # If there are active hits, we only generate candidates that cover at least one active hit.
    # This drastically reduces the search space and enforces the "Must Cover" rule implicitly
    # (because if a cell has 0 probability of being part of a ship that covers hits, it won't be picked).
    
    heat_map = [[0] * N for _ in range(N)]
    
    for size in remaining_sizes:
        # Determine valid orientations
        # Horizontal
        for r in range(N):
            for c in range(N - size + 1):
                valid = True
                covers_hit = False
                for k in range(size):
                    nr, nc = r, c + k
                    if (nr, nc) in misses:
                        valid = False
                        break
                    if (nr, nc) in active_hits:
                        covers_hit = True
                if valid:
                    # If we have active hits, we must cover at least one
                    if active_hits and not covers_hit:
                        continue
                    # Add to heat map
                    for k in range(size):
                        nr, nc = r, c + k
                        heat_map[nr][nc] += 1
                        
        # Vertical
        for c in range(N):
            for r in range(N - size + 1):
                valid = True
                covers_hit = False
                for k in range(size):
                    nr, nc = r + k, c
                    if (nr, nc) in misses:
                        valid = False
                        break
                    if (nr, nc) in active_hits:
                        covers_hit = True
                if valid:
                    if active_hits and not covers_hit:
                        continue
                    for k in range(size):
                        nr, nc = r + k, c
                        heat_map[nr][nc] += 1

    # 5. Selection
    # We want to pick an unknown cell with the highest heat.
    # We must not pick a cell that is already a hit or miss (though policy forbids firing at known cells).
    max_heat = -1
    candidates = []
    
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0: # Only unknown cells
                h = heat_map[r][c]
                if h > max_heat:
                    max_heat = h
                    candidates = [(r, c)]
                elif h == max_heat:
                    candidates.append((r, c))
    
    if candidates:
        return random.choice(candidates)
    
    # 6. Fallback: Parity / Checkerboard
    # If heat map fails (e.g., all unknown cells have 0 heat due to strict constraints or late game),
    # pick a random unknown cell, preferably on a checkerboard pattern to minimize misses on 2-length ships.
    # "Checkerboard" means (r+c) % 2 == 0 (or 1).
    # We prefer the pattern that has more space. Usually, since ships are length >= 2, 
    # hitting every other cell is optimal for hunting.
    
    unknowns = list(unknown_cells)
    if not unknowns:
        # Should not happen unless board is full
        return (0, 0)
        
    # Prefer parity (0,0) based on density
    # Usually (r+c) % 2 == 0 is slightly denser (27 vs 23 on 10x10) or vice versa.
    # Let's check which parity has more unknowns left.
    p0 = [c for c in unknowns if (c[0]+c[1]) % 2 == 0]
    p1 = [c for c in unknowns if (c[0]+c[1]) % 2 == 1]
    
    if p0 and (not p1 or len(p0) >= len(p1)):
        return random.choice(p0)
    else:
        return random.choice(p1)
