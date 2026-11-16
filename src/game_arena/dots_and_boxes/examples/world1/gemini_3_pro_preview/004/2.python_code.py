
import numpy as np
import copy

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Determines the next move for a 4x4 Dots and Boxes game.
    
    Strategy:
    1. Score immediately if possible (Greedy Capture).
    2. If no score, play a 'safe' move that doesn't let the opponent score (doesn't create a box with 3 sides).
       - Heuristic: Prefer moves that touch boxes with fewer current sides.
    3. If forced to give points (all moves unsafe), pick the move that minimizes the number of boxes
       the opponent can take in the resulting chain.
    """
    
    # Grid dimensions
    R_BOX, C_BOX = 4, 4
    
    # --- Helper Functions ---

    def get_box_sides(r, c, h, v):
        """Returns the number of drawn sides for box (r, c)."""
        # Box (r, c) is bounded by:
        # Top: H[r, c]
        # Bottom: H[r+1, c]
        # Left: V[r, c]
        # Right: V[r, c+1]
        sides = 0
        if h[r, c] != 0: sides += 1
        if h[r+1, c] != 0: sides += 1
        if v[r, c] != 0: sides += 1
        if v[r, c+1] != 0: sides += 1
        return sides

    def get_legal_moves(h, v):
        """Returns a list of legal moves as (r, c, type)."""
        moves = []
        # Horizontal edges: 5 rows, 4 cols
        for r in range(5):
            for c in range(4):
                if h[r, c] == 0:
                    moves.append((r, c, 'H'))
        # Vertical edges: 4 rows, 5 cols
        for r in range(4):
            for c in range(5):
                if v[r, c] == 0:
                    moves.append((r, c, 'V'))
        return moves

    def get_outcome_class(move, h, v):
        """
        Classifies a move into:
        - 'CAPTURE': Completes a box (4 sides).
        - 'UNSAFE': Does not complete a box, but creates a box with 3 sides.
        - 'SAFE': Leaves adjacent boxes with <= 2 sides.
        
        Also returns a heuristic score for SAFE moves (lower is better).
        """
        r_edge, c_edge, orient = move
        
        # Identify adjacent boxes
        adj_boxes = []
        if orient == 'H':
            # Horizontal edge at row r, col c separates box (r-1, c) and (r, c)
            # Valid boxes are rows 0..3
            if r_edge > 0: adj_boxes.append((r_edge - 1, c_edge))
            if r_edge < 4: adj_boxes.append((r_edge, c_edge))
        else:
            # Vertical edge at row r, col c separates box (r, c-1) and (r, c)
            # Valid boxes are cols 0..3
            if c_edge > 0: adj_boxes.append((r_edge, c_edge - 1))
            if c_edge < 4: adj_boxes.append((r_edge, c_edge))
            
        is_capture = False
        is_unsafe = False
        max_sides_after = 0
        
        for br, bc in adj_boxes:
            s = get_box_sides(br, bc, h, v)
            # Since the move adds a side, new sides = s + 1
            new_s = s + 1
            
            if new_s == 4:
                is_capture = True
            elif new_s == 3:
                is_unsafe = True
            
            if new_s > max_sides_after:
                max_sides_after = new_s

        if is_capture:
            return 'CAPTURE', 0
        elif is_unsafe:
            return 'UNSAFE', 0
        else:
            # For safe moves, we prefer those where max_sides_after is small.
            # 1 is best (0->1), 2 is worse (1->2).
            return 'SAFE', max_sides_after

    def count_chain_loss(h_sim, v_sim):
        """
        Simulates the opponent's greedy moves starting from current state.
        Returns the number of boxes captured by the opponent.
        """
        captured_count = 0
        h_temp = h_sim.copy()
        v_temp = v_sim.copy()
        
        while True:
            progress = False
            # Scan all boxes to see if any have 3 sides
            # This is a simplistic simulation: finding any 3-sided box and filling it
            # The opponent takes ALL available 3-chains.
            
            # Identify all fillable boxes
            candidates = []
            for r in range(4):
                for c in range(4):
                    # Check if already taken?
                    # We can infer taken by checking if sides == 4
                    # But we only care about those with exactly 3 sides currently
                    s = get_box_sides(r, c, h_temp, v_temp)
                    if s == 3:
                        candidates.append((r, c))
            
            if not candidates:
                break
                
            # Assume opponent takes all available captures
            # Note: In real game, they take one, recurse. But pure greedy just takes everything iteratively.
            captured_count += len(candidates)
            progress = True
            
            for (r, c) in candidates:
                # Find the missing edge
                # Top
                if h_temp[r, c] == 0: h_temp[r, c] = -1
                # Bottom
                elif h_temp[r+1, c] == 0: h_temp[r+1, c] = -1
                # Left
                elif v_temp[r, c] == 0: v_temp[r, c] = -1
                # Right
                elif v_temp[r, c+1] == 0: v_temp[r, c+1] = -1
        
        return captured_count

    # --- Main Logic ---

    legal_moves = get_legal_moves(horizontal, vertical)
    if not legal_moves:
        return "" # Should not happen based on constraints

    capture_moves = []
    safe_moves = []   # List of (score, move)
    unsafe_moves = [] # List of move

    for move in legal_moves:
        cat, score = get_outcome_class(move, horizontal, vertical)
        if cat == 'CAPTURE':
            capture_moves.append(move)
        elif cat == 'SAFE':
            safe_moves.append((score, move))
        else: # UNSAFE
            unsafe_moves.append(move)

    # Priority 1: Captures
    if capture_moves:
        # Just take the first available capture. 
        # (Advanced logic could check for double-cross setups, but greedy is strong/robust)
        best_move = capture_moves[0]
        return f"{best_move[0]},{best_move[1]},{best_move[2]}"

    # Priority 2: Safe Moves
    if safe_moves:
        # Sort safe moves by score (lower max_sides_after is better)
        # Random shuffle first to vary play if scores are equal
        np.random.shuffle(safe_moves)
        safe_moves.sort(key=lambda x: x[0])
        best_move = safe_moves[0][1]
        return f"{best_move[0]},{best_move[1]},{best_move[2]}"

    # Priority 3: Unsafe Moves (Sacrifice)
    # We must play a move that allows opponent to score. Minimize their score.
    best_sacrifice = None
    min_loss = float('inf')
    
    # Shuffle to not introduce bias in equal logical branches
    idx_list = np.arange(len(unsafe_moves))
    np.random.shuffle(idx_list)
    
    for idx in idx_list:
        move = unsafe_moves[idx]
        
        # Simulate making this move
        h_sim = horizontal.copy()
        v_sim = vertical.copy()
        r, c, orient = move
        
        # We play (1)
        if orient == 'H': h_sim[r, c] = 1
        else: v_sim[r, c] = 1
        
        # Count how many box opponent can get greedily
        loss = count_chain_loss(h_sim, v_sim)
        
        if loss < min_loss:
            min_loss = loss
            best_sacrifice = move
            # Optimization: if loss is small (e.g. 1 or 2), it's likely the best we get
            if min_loss <= 2:
                break
    
    if best_sacrifice:
        return f"{best_sacrifice[0]},{best_sacrifice[1]},{best_sacrifice[2]}"
        
    # Fallback (should be covered by unsafe case)
    fallback = legal_moves[0]
    return f"{fallback[0]},{fallback[1]},{fallback[2]}"
