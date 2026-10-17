
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
        if r < 0 or r >= 4 or c < 0 or c >= 4:
            return -1  # Invalid box
        count = 0
        if horizontal[r, c] != 0: count += 1      # Top
        if horizontal[r+1, c] != 0: count += 1    # Bottom
        if vertical[r, c] != 0: count += 1        # Left
        if vertical[r, c+1] != 0: count += 1      # Right
        return count
    
    def boxes_affected_by_move(r, c, d):
        boxes = []
        if d == 'H':
            if r > 0: boxes.append((r-1, c))  # Box above
            if r < 4: boxes.append((r, c))    # Box below
        else:  # V
            if c > 0: boxes.append((r, c-1))  # Box to left
            if c < 4: boxes.append((r, c))    # Box to right
        return [(br, bc) for br, bc in boxes if 0 <= br < 4 and 0 <= bc < 4]
    
    def move_completes_box(r, c, d):
        boxes = boxes_affected_by_move(r, c, d)
        for br, bc in boxes:
            if capture[br, bc] == 0 and count_box_sides(br, bc) == 3:
                return True
        return False
    
    def move_creates_three_sided(r, c, d):
        boxes = boxes_affected_by_move(r, c, d)
        for br, bc in boxes:
            if capture[br, bc] == 0 and count_box_sides(br, bc) == 2:
                return True
        return False
    
    def count_boxes_completed(r, c, d):
        boxes = boxes_affected_by_move(r, c, d)
        count = 0
        for br, bc in boxes:
            if capture[br, bc] == 0 and count_box_sides(br, bc) == 3:
                count += 1
        return count
    
    legal_moves = get_legal_moves()
    
    if not legal_moves:
        return "0,0,H"  # Should never happen
    
    # Priority 1: Moves that complete boxes (we get another turn)
    capturing_moves = [(m, count_boxes_completed(*m)) for m in legal_moves if move_completes_box(*m)]
    if capturing_moves:
        # Prefer moves that capture more boxes
        capturing_moves.sort(key=lambda x: -x[1])
        m = capturing_moves[0][0]
        return f"{m[0]},{m[1]},{m[2]}"
    
    # Priority 2: Safe moves (don't create 3-sided boxes)
    safe_moves = [m for m in legal_moves if not move_creates_three_sided(*m)]
    if safe_moves:
        # Among safe moves, prefer those that affect boxes with fewer sides
        def min_sides(m):
            boxes = boxes_affected_by_move(*m)
            if not boxes:
                return 0
            return min(count_box_sides(br, bc) for br, bc in boxes)
        safe_moves.sort(key=min_sides)
        m = safe_moves[0]
        return f"{m[0]},{m[1]},{m[2]}"
    
    # Priority 3: All moves are dangerous - pick one that gives away fewest boxes
    # Try to find the shortest chain to sacrifice
    def count_chain_size(r, c, d):
        # Simplified: just count how many 3-sided boxes this creates
        boxes = boxes_affected_by_move(r, c, d)
        count = 0
        for br, bc in boxes:
            if capture[br, bc] == 0 and count_box_sides(br, bc) == 2:
                count += 1
        return count
    
    legal_moves.sort(key=lambda m: count_chain_size(*m))
    m = legal_moves[0]
    return f"{m[0]},{m[1]},{m[2]}"
