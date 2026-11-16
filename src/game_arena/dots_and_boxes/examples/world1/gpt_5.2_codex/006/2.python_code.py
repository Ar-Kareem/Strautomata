
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Choose a move for 4x4 Dots and Boxes.
    Returns 'row,col,dir' where dir is 'H' or 'V'.
    """

    # Helper: count sides of a box at (r,c)
    def box_sides(r, c):
        sides = 0
        if horizontal[r, c] != 0: sides += 1
        if horizontal[r+1, c] != 0: sides += 1
        if vertical[r, c] != 0: sides += 1
        if vertical[r, c+1] != 0: sides += 1
        return sides

    # Evaluate move: returns (completed_boxes, new_three_sides)
    def evaluate_move(r, c, d):
        completed = 0
        threes = 0
        if d == 'H':
            # affects box above and/or below
            if r > 0:
                br, bc = r-1, c
                if capture[br, bc] == 0:
                    sides = box_sides(br, bc)
                    if sides + 1 == 4:
                        completed += 1
                    elif sides + 1 == 3:
                        threes += 1
            if r < 4:
                br, bc = r, c
                if capture[br, bc] == 0:
                    sides = box_sides(br, bc)
                    if sides + 1 == 4:
                        completed += 1
                    elif sides + 1 == 3:
                        threes += 1
        else:  # 'V'
            # affects box left and/or right
            if c > 0:
                br, bc = r, c-1
                if capture[br, bc] == 0:
                    sides = box_sides(br, bc)
                    if sides + 1 == 4:
                        completed += 1
                    elif sides + 1 == 3:
                        threes += 1
            if c < 4:
                br, bc = r, c
                if capture[br, bc] == 0:
                    sides = box_sides(br, bc)
                    if sides + 1 == 4:
                        completed += 1
                    elif sides + 1 == 3:
                        threes += 1
        return completed, threes

    # Generate legal moves
    legal_moves = []
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] == 0:
                legal_moves.append((r, c, 'H'))
    for r in range(4):
        for c in range(5):
            if vertical[r, c] == 0:
                legal_moves.append((r, c, 'V'))

    # Safety fallback (should never be empty before game end)
    if not legal_moves:
        return "0,0,H"

    # Evaluate all moves
    evals = []
    for r, c, d in legal_moves:
        completed, threes = evaluate_move(r, c, d)
        evals.append((completed, threes, r, c, d))

    # 1) If any capturing move exists, take the best one
    max_completed = max(e[0] for e in evals)
    if max_completed > 0:
        best = [e for e in evals if e[0] == max_completed]
        # Tie-breaker: minimize new three-sides
        best.sort(key=lambda x: x[1])
        _, _, r, c, d = best[0]
        return f"{r},{c},{d}"

    # 2) Otherwise, avoid creating three-sided boxes
    safe = [e for e in evals if e[1] == 0]
    if safe:
        _, _, r, c, d = safe[0]
        return f"{r},{c},{d}"

    # 3) If no safe move, choose the least bad (minimize threes)
    evals.sort(key=lambda x: x[1])
    _, _, r, c, d = evals[0]
    return f"{r},{c},{d}"
