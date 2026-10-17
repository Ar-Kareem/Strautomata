
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # Sizes: horizontal is 5x4(actually 5x5 provided), vertical is 4x5(actually 5x5)
    # 4x4 box grid means:
    # Horizontal edges: row 0-4, col 0-3
    # Vertical edges: row 0-3, col 0-4
    
    def count_sides(r, c):
        # Count filled sides for box at (r, c)
        count = 0
        if horizontal[r, c] != 0: count += 1
        if horizontal[r+1, c] != 0: count += 1
        if vertical[r, c] != 0: count += 1
        if vertical[r, c+1] != 0: count += 1
        return count

    def get_legal_moves():
        legals = []
        for r in range(5):
            for c in range(4):
                if horizontal[r, c] == 0:
                    legals.append((r, c, 'H'))
        for r in range(4):
            for c in range(5):
                if vertical[r, c] == 0:
                    legals.append((r, c, 'V'))
        return legals

    def evaluate_move(r, c, d):
        completed_boxes = 0
        max_sides_created = 0 # Max sides any adjacent box will have after this move
        
        if d == 'H':
            # Horizontal edge affects box above (r-1, c) and box below (r, c)
            adj_boxes = []
            if r > 0: adj_boxes.append((r - 1, c))
            if r < 4: adj_boxes.append((r, c))
            
            for br, bc in adj_boxes:
                s = count_sides(br, bc)
                if s == 3: completed_boxes += 1
                max_sides_created = max(max_sides_created, s + 1)
        else:
            # Vertical edge affects box left (r, c-1) and box right (r, c)
            adj_boxes = []
            if c > 0: adj_boxes.append((r, c - 1))
            if c < 4: adj_boxes.append((r, c))
            
            for br, bc in adj_boxes:
                s = count_sides(br, bc)
                if s == 3: completed_boxes += 1
                max_sides_created = max(max_sides_created, s + 1)
                
        return completed_boxes, max_sides_created

    moves = get_legal_moves()
    
    scoring_moves = []
    safe_moves = []
    other_moves = []
    
    for r, c, d in moves:
        completed, max_sides = evaluate_move(r, c, d)
        if completed > 0:
            scoring_moves.append(((r, c, d), completed))
        elif max_sides < 3:
            safe_moves.append((r, c, d))
        else:
            other_moves.append((r, c, d))
            
    # 1. Take captures (prioritize double captures)
    if scoring_moves:
        scoring_moves.sort(key=lambda x: x[1], reverse=True)
        best_move = scoring_moves[0][0]
        return f"{best_move[0]},{best_move[1]},{best_move[2]}"
    
    # 2. Play safe moves (don't set up the opponent)
    if safe_moves:
        # Simple heuristic: pick a safe move
        best_move = safe_moves[0]
        return f"{best_move[0]},{best_move[1]},{best_move[2]}"
        
    # 3. If forced, just play any legal move
    if moves:
        best_move = moves[0]
        return f"{best_move[0]},{best_move[1]},{best_move[2]}"

    return "0,0,H" # Fallback
