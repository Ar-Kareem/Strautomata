
import numpy as np
import random

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Decides the next move for Dots and Boxes (4x4 box grid).
    
    Logic:
    1. CAPTURE: If a move completes a box, take it immediately.
    2. SAFE: If no capture, choose a random move that does not set any box to 3 sides.
    3. SACRIFICE: If forced to give captures, choose the move that gives the opponent 
       the fewest total boxes (simulating the resulting chain reaction).
    """
    
    # Grid constants for 4x4 boxes
    # Horizontal edges: 5 rows (0-4), 4 cols (0-3)
    # Vertical edges: 4 rows (0-3), 5 cols (0-4)
    NB_ROWS, NB_COLS = 4, 4
    
    # 1. Analyze the current state of boxes
    # box_sides[r, c] stores the number of drawn edges for box at row r, col c.
    box_sides = np.zeros((NB_ROWS, NB_COLS), dtype=int)
    
    for r in range(NB_ROWS):
        for c in range(NB_COLS):
            count = 0
            if horizontal[r, c] != 0: count += 1     # Top
            if horizontal[r+1, c] != 0: count += 1   # Bottom
            if vertical[r, c] != 0: count += 1       # Left
            if vertical[r, c+1] != 0: count += 1     # Right
            box_sides[r, c] = count

    # 2. Identify all legal moves
    moves = []
    # Horizontal candidates: rows 0..4, cols 0..3
    for r in range(NB_ROWS + 1):
        for c in range(NB_COLS):
            if horizontal[r, c] == 0:
                moves.append((r, c, 'H'))
    # Vertical candidates: rows 0..3, cols 0..4
    for r in range(NB_ROWS):
        for c in range(NB_COLS + 1):
            if vertical[r, c] == 0:
                moves.append((r, c, 'V'))
                
    if not moves:
        return ""

    # 3. Categorize moves
    capturing_moves = []
    safe_moves = []
    unsafe_moves = []
    
    for m in moves:
        r, c, mtype = m
        is_capture = False
        is_giveaway = False
        
        # Check adjacent boxes for this edge
        # If any adjacent box has 3 sides, this move captures it.
        # If any adjacent box has 2 sides, this move makes it 3 (giveaway/unsafe).
        
        if mtype == 'H':
            # Box above: (r-1, c), Box below: (r, c)
            if r > 0:
                if box_sides[r-1, c] == 3: is_capture = True
                if box_sides[r-1, c] == 2: is_giveaway = True
            if r < NB_ROWS:
                if box_sides[r, c] == 3: is_capture = True
                if box_sides[r, c] == 2: is_giveaway = True
        else: # 'V'
            # Box left: (r, c-1), Box right: (r, c)
            if c > 0:
                if box_sides[r, c-1] == 3: is_capture = True
                if box_sides[r, c-1] == 2: is_giveaway = True
            if c < NB_COLS:
                if box_sides[r, c] == 3: is_capture = True
                if box_sides[r, c] == 2: is_giveaway = True
                
        if is_capture:
            capturing_moves.append(m)
        elif is_giveaway:
            unsafe_moves.append(m)
        else:
            safe_moves.append(m)

    # 4. Execute Strategy
    
    # Priority 1: Capture
    if capturing_moves:
        # Taking any capture is usually optimal (extra turn).
        choice = random.choice(capturing_moves)
        return f"{choice[0]},{choice[1]},{choice[2]}"
        
    # Priority 2: Safe Move
    if safe_moves:
        # Pick any safe move. 
        choice = random.choice(safe_moves)
        return f"{choice[0]},{choice[1]},{choice[2]}"
        
    # Priority 3: Minimize Sacrifice
    # We must play an unsafe move. We simulate the opponent's outcome for each.
    best_move = unsafe_moves[0]
    min_loss = 1000  # minimize opponent's chained captures
    
    # Shuffle to ensure random tie-breaking
    random.shuffle(unsafe_moves)
    
    for m in unsafe_moves:
        mr, mc, mtype = m
        
        # Copy state for simulation
        sim_h = horizontal.copy()
        sim_v = vertical.copy()
        sim_sides = box_sides.copy()
        
        # 1. Apply our move (the sacrifice)
        if mtype == 'H':
            sim_h[mr, mc] = 1
            if mr > 0: sim_sides[mr-1, mc] += 1
            if mr < NB_ROWS: sim_sides[mr, mc] += 1
        else:
            sim_v[mr, mc] = 1
            if mc > 0: sim_sides[mr, mc-1] += 1
            if mc < NB_COLS: sim_sides[mr, mc] += 1
            
        # 2. Identify boxes that become capturable (3 sides)
        stack = []
        for r in range(NB_ROWS):
            for c in range(NB_COLS):
                if sim_sides[r, c] == 3:
                    stack.append((r, c))
        
        # 3. Simulate opponent's greedy chain capture
        loss = 0
        visited = set(stack)
        
        while stack:
            br, bc = stack.pop()
            loss += 1
            
            # Opponent claims box (br, bc) by filling the missing edge
            # Find missing edge
            missing = None
            if sim_h[br, bc] == 0: missing = (br, bc, 'H')
            elif sim_h[br+1, bc] == 0: missing = (br+1, bc, 'H')
            elif sim_v[br, bc] == 0: missing = (br, bc, 'V')
            elif sim_v[br, bc+1] == 0: missing = (br, bc+1, 'V')
            
            if missing:
                er, ec, etype = missing
                # Fill edge
                if etype == 'H':
                    sim_h[er, ec] = -1
                    # Update neighbors (Up/Down)
                    neighbors = []
                    if er > 0: neighbors.append((er-1, ec))
                    if er < NB_ROWS: neighbors.append((er, ec))
                    
                    for nr, nc in neighbors:
                        if (nr, nc) == (br, bc): continue
                        sim_sides[nr, nc] += 1
                        if sim_sides[nr, nc] == 3 and (nr, nc) not in visited:
                            visited.add((nr, nc))
                            stack.append((nr, nc))
                else:
                    sim_v[er, ec] = -1
                    # Update neighbors (Left/Right)
                    neighbors = []
                    if ec > 0: neighbors.append((er, ec-1))
                    if ec < NB_COLS: neighbors.append((er, ec))
                    
                    for nr, nc in neighbors:
                        if (nr, nc) == (br, bc): continue
                        sim_sides[nr, nc] += 1
                        if sim_sides[nr, nc] == 3 and (nr, nc) not in visited:
                            visited.add((nr, nc))
                            stack.append((nr, nc))
                            
        if loss < min_loss:
            min_loss = loss
            best_move = m
            
    return f"{best_move[0]},{best_move[1]},{best_move[2]}"
