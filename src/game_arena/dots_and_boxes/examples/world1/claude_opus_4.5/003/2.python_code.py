
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    def get_legal_moves():
        moves = []
        for r in range(5):
            for c in range(4):
                if horizontal[r, c] == 0:
                    moves.append((r, c, 'H'))
        for r in range(4):
            for c in range(5):
                if vertical[r, c] == 0:
                    moves.append((r, c, 'V'))
        return moves
    
    def count_box_sides(r, c):
        """Count how many sides box (r,c) has filled (0 <= r,c < 4)"""
        count = 0
        if horizontal[r, c] != 0:  # top
            count += 1
        if horizontal[r+1, c] != 0:  # bottom
            count += 1
        if vertical[r, c] != 0:  # left
            count += 1
        if vertical[r, c+1] != 0:  # right
            count += 1
        return count
    
    def get_affected_boxes(move):
        """Return list of boxes affected by a move"""
        r, c, d = move
        boxes = []
        if d == 'H':
            # Horizontal edge at (r, c) affects box above (r-1, c) and below (r, c)
            if r > 0 and c < 4:
                boxes.append((r-1, c))
            if r < 4 and c < 4:
                boxes.append((r, c))
        else:  # V
            # Vertical edge at (r, c) affects box left (r, c-1) and right (r, c)
            if c > 0 and r < 4:
                boxes.append((r, c-1))
            if c < 4 and r < 4:
                boxes.append((r, c))
        return boxes
    
    def evaluate_move(move):
        """
        Returns (boxes_captured, boxes_given_away)
        boxes_captured: number of boxes we complete with this move
        boxes_given_away: number of boxes that will have 3 sides after this move
        """
        affected = get_affected_boxes(move)
        captured = 0
        given_away = 0
        
        for (br, bc) in affected:
            if capture[br, bc] != 0:
                continue  # already captured
            sides = count_box_sides(br, bc)
            if sides == 3:
                captured += 1  # we complete it
            elif sides == 2:
                given_away += 1  # becomes 3-sided, opponent can take
        
        return captured, given_away
    
    legal_moves = get_legal_moves()
    
    if not legal_moves:
        return "0,0,H"  # shouldn't happen, but safety fallback
    
    # Categorize moves
    capturing_moves = []
    safe_moves = []
    risky_moves = []
    
    for move in legal_moves:
        captured, given = evaluate_move(move)
        if captured > 0:
            capturing_moves.append((move, captured, given))
        elif given == 0:
            safe_moves.append((move, captured, given))
        else:
            risky_moves.append((move, captured, given))
    
    # Priority 1: Take any capturing move (prefer more captures)
    if capturing_moves:
        capturing_moves.sort(key=lambda x: -x[1])
        best = capturing_moves[0][0]
        return f"{best[0]},{best[1]},{best[2]}"
    
    # Priority 2: Safe moves (don't give opponent any boxes)
    if safe_moves:
        # Prefer moves that don't advance boxes to 2 sides
        best = safe_moves[0][0]
        return f"{best[0]},{best[1]},{best[2]}"
    
    # Priority 3: Must give away boxes - minimize damage
    if risky_moves:
        # Sort by fewest boxes given away
        risky_moves.sort(key=lambda x: x[2])
        best = risky_moves[0][0]
        return f"{best[0]},{best[1]},{best[2]}"
    
    # Fallback (should not reach here)
    move = legal_moves[0]
    return f"{move[0]},{move[1]},{move[2]}"
