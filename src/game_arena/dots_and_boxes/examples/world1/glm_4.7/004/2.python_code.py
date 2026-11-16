
import numpy as np
import random

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Dots and Boxes Policy for a 4x4 grid.
    
    Args:
        horizontal: 5x5 array, 1 if horizontal edge at (r,c) is drawn.
        vertical: 5x5 array, 1 if vertical edge at (r,c) is drawn.
        capture: 4x4 (or 5x5) array, 1 if box (r,c) is claimed by us, -1 by opponent.
    
    Returns:
        str: Move in 'row,col,dir' format.
    """
    
    # Grid dimensions: 4x4 boxes means 5x5 dots.
    # Horizontal edges: 5 rows of dots * 4 horizontal edges per row.
    # Vertical edges: 4 rows of dots * 5 vertical edges per row.
    ROWS, COLS = 4, 4
    
    # Helper to count sides of a box (r, c) where r, c are box coordinates [0..3]
    def count_box_sides(br, bc, h_arr, v_arr):
        # Box (br, bc) is bounded by:
        # Top: h_arr[br, bc]
        # Bottom: h_arr[br+1, bc]
        # Left: v_arr[br, bc]
        # Right: v_arr[br, bc+1]
        sides = 0
        if h_arr[br, bc] != 0: sides += 1
        if h_arr[br+1, bc] != 0: sides += 1
        if v_arr[br, bc] != 0: sides += 1
        if v_arr[br, bc+1] != 0: sides += 1
        return sides

    # Helper to evaluate the outcome of a potential move
    def evaluate_move(r, c, direction):
        """
        Returns a tuple: (captures, new_3_siders, total_new_sides)
        - captures: number of boxes completed by this move.
        - new_3_siders: number of unclaimed boxes that become 3-sided (bad).
        - total_new_sides: sum of sides of affected boxes (heuristic for safety).
        """
        h_sim = horizontal.copy()
        v_sim = vertical.copy()
        
        captures = 0
        new_3_siders = 0
        total_new_sides = 0
        
        # Apply move to simulated board
        if direction == 'H':
            h_sim[r, c] = 1
            # Affected boxes: Top (r, c) and Bottom (r-1, c)
            affected_boxes = []
            if r < ROWS: affected_boxes.append((r, c))
            if r > 0:    affected_boxes.append((r-1, c))
        else: # 'V'
            v_sim[r, c] = 1
            # Affected boxes: Left (r, c) and Right (r, c-1)
            affected_boxes = []
            if c < COLS: affected_boxes.append((r, c))
            if c > 0:    affected_boxes.append((r, c-1))
            
        for br, bc in affected_boxes:
            # Only consider boxes that are not already claimed
            if capture[br, bc] == 0:
                sides = count_box_sides(br, bc, h_sim, v_sim)
                total_new_sides += sides
                
                if sides == 4:
                    captures += 1
                elif sides == 3:
                    new_3_siders += 1
                    
        return captures, new_3_siders, total_new_sides

    # --- Generate all legal moves ---
    legal_moves = []
    
    # Horizontal moves: valid range r[0..4], c[0..3]
    for r in range(ROWS + 1):
        for c in range(COLS):
            if horizontal[r, c] == 0:
                legal_moves.append({'r': r, 'c': c, 'd': 'H'})
                
    # Vertical moves: valid range r[0..3], c[0..4]
    for r in range(ROWS):
        for c in range(COLS + 1):
            if vertical[r, c] == 0:
                legal_moves.append({'r': r, 'c': c, 'd': 'V'})

    if not legal_moves:
        # Should not happen in a running game, but fail-safe
        return "0,0,H"

    # --- Evaluate all legal moves ---
    # We structure evaluation to find the best move based on priorities
    best_score = -float('inf')
    candidates = []
    
    for move in legal_moves:
        r, c, d = move['r'], move['c'], move['d']
        caps, threes, sides_sum = evaluate_move(r, c, d)
        
        # Heuristic Scoring:
        # Priority 1: Maximize captures (Huge weight)
        # Priority 2: Minimize new 3-siders (Negative weight)
        # Priority 3: Minimize total sides on affected boxes (Slight negative weight to stay safe)
        # Note: If threes > 0, we are in trouble. Minimizing sides_sum is less important than minimizing threes.
        
        score = caps * 100 - threes * 10 - (sides_sum * 0.1)
        
        # Re-evaluating logic for strict tiering to be safe
        
        move['caps'] = caps
        move['threes'] = threes
        move['sides_sum'] = sides_sum
        move['score'] = score

    # --- Selection Strategy ---
    
    # 1. Filter moves that capture the most boxes
    max_caps = max(m['caps'] for m in legal_moves)
    capturing_moves = [m for m in legal_moves if m['caps'] == max_caps]
    
    if max_caps > 0:
        # We have a capture! Randomly choose among the best captures
        choice = random.choice(capturing_moves)
        return f"{choice['r']},{choice['c']},{choice['d']}"
    
    # 2. No captures. Filter moves that create the fewest 3-sided boxes
    min_threes = min(m['threes'] for m in legal_moves)
    safeish_moves = [m for m in legal_moves if m['threes'] == min_threes]
    
    # 3. Among these, pick moves that minimize the 'progress' (total sides)
    # This prefers playing on empty boxes rather than filling up 1-sided or 2-sided boxes.
    min_sides_sum = min(m['sides_sum'] for m in safeish_moves)
    best_moves = [m for m in safeish_moves if m['sides_sum'] == min_sides_sum]
    
    # 4. Return a random best move to ensure non-determinism
    choice = random.choice(best_moves)
    return f"{choice['r']},{choice['c']},{choice['d']}"
