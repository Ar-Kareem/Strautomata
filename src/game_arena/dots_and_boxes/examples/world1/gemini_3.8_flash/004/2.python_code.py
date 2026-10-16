
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Returns the next move for 4x4 Dots and Boxes.
    Move format: 'row,col,dir' where dir in ('H', 'V').
    """
    H = horizontal
    V = vertical

    # Helper: get sides count for box (r, c) in 0..3
    def box_sides(r: int, c: int, h_grid, v_grid) -> int:
        count = 0
        if h_grid[r, c] != 0: count += 1
        if h_grid[r + 1, c] != 0: count += 1
        if v_grid[r, c] != 0: count += 1
        if v_grid[r, c + 1] != 0: count += 1
        return count

    # Helper: count how many boxes drawing an edge completes
    def completed_boxes(r: int, c: int, orientation: str, h_grid, v_grid) -> int:
        completed = 0
        if orientation == 'H':
            # Box above (r - 1, c)
            if r > 0:
                if (h_grid[r - 1, c] != 0 and 
                    v_grid[r - 1, c] != 0 and 
                    v_grid[r - 1, c + 1] != 0):
                    completed += 1
            # Box below (r, c)
            if r < 4:
                if (h_grid[r + 1, c] != 0 and 
                    v_grid[r, c] != 0 and 
                    v_grid[r, c + 1] != 0):
                    completed += 1
        else:  # 'V'
            # Box to the left (r, c - 1)
            if c > 0:
                if (v_grid[r, c - 1] != 0 and 
                    h_grid[r, c - 1] != 0 and 
                    h_grid[r + 1, c - 1] != 0):
                    completed += 1
            # Box to the right (r, c)
            if c < 4:
                if (v_grid[r, c + 1] != 0 and 
                    h_grid[r, c] != 0 and 
                    h_grid[r + 1, c] != 0):
                    completed += 1
        return completed

    # Helper: check if drawing edge creates a box with exactly 3 sides filled
    def creates_three_sides(r: int, c: int, orientation: str, h_grid, v_grid) -> bool:
        if orientation == 'H':
            if r > 0 and box_sides(r - 1, c, h_grid, v_grid) == 2:
                return True
            if r < 4 and box_sides(r, c, h_grid, v_grid) == 2:
                return True
        else:
            if c > 0 and box_sides(r, c - 1, h_grid, v_grid) == 2:
                return True
            if c < 4 and box_sides(r, c, h_grid, v_grid) == 2:
                return True
        return False

    # Collect standard legal moves
    capturing_moves = []
    safe_moves = []
    risky_moves = []

    # Standard 4x4 grid edges
    all_standard_moves = []
    for r in range(5):
        for c in range(4):
            if H[r, c] == 0:
                all_standard_moves.append((r, c, 'H'))
    for r in range(4):
        for c in range(5):
            if V[r, c] == 0:
                all_standard_moves.append((r, c, 'V'))

    # Fallback to any remaining 0 in the 5x5 arrays if no standard move is available
    if not all_standard_moves:
        for r in range(5):
            for c in range(5):
                if H[r, c] == 0:
                    return f"{r},{c},H"
                if V[r, c] == 0:
                    return f"{r},{c},V"

    for (r, c, ori) in all_standard_moves:
        caps = completed_boxes(r, c, ori, H, V)
        if caps > 0:
            capturing_moves.append((caps, r, c, ori))
        elif not creates_three_sides(r, c, ori, H, V):
            safe_moves.append((r, c, ori))
        else:
            risky_moves.append((r, c, ori))

    # 1. Take captures if available
    if capturing_moves:
        # Prefer taking captures that complete 2 boxes first, or any capture
        capturing_moves.sort(key=lambda x: x[0], reverse=True)
        _, r, c, ori = capturing_moves[0]
        return f"{r},{c},{ori}"

    # 2. Pick a safe move that gives the least influence towards opponent chains
    if safe_moves:
        def safe_move_quality(move):
            r, c, ori = move
            # Prefer edges touching boxes with fewer sides (0 is best, then 1)
            sides_sum = 0
            if ori == 'H':
                if r > 0: sides_sum += box_sides(r - 1, c, H, V)
                if r < 4: sides_sum += box_sides(r, c, H, V)
            else:
                if c > 0: sides_sum += box_sides(r, c - 1, H, V)
                if c < 4: sides_sum += box_sides(r, c, H, V)
            return sides_sum

        safe_moves.sort(key=safe_move_quality)
        r, c, ori = safe_moves[0]
        return f"{r},{c},{ori}"

    # 3. If no safe moves, find the least damaging risky move
    # Count how many boxes an opponent can immediately capture if we make this move
    def evaluate_chain_damage(move):
        r, c, ori = move
        temp_H = H.copy()
        temp_V = V.copy()
        if ori == 'H':
            temp_H[r, c] = 1
        else:
            temp_V[r, c] = 1

        # Simulate greedy opponent captures
        boxes_given = 0
        changed = True
        while changed:
            changed = False
            for br in range(4):
                for bc in range(4):
                    if box_sides(br, bc, temp_H, temp_V) == 3:
                        # Find the missing edge and fill it
                        if temp_H[br, bc] == 0: temp_H[br, bc] = -1
                        elif temp_H[br + 1, bc] == 0: temp_H[br + 1, bc] = -1
                        elif temp_V[br, bc] == 0: temp_V[br, bc] = -1
                        elif temp_V[br, bc + 1] == 0: temp_V[br, bc + 1] = -1
                        boxes_given += 1
                        changed = True
                        break
                if changed:
                    break
        return boxes_given

    risky_moves.sort(key=evaluate_chain_damage)
    r, c, ori = risky_moves[0]
    return f"{r},{c},{ori}"
