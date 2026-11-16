
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    legal_moves = []
    for r in range(5):
        for c in range(5):
            if horizontal[r, c] == 0:
                legal_moves.append((r, c, 'H'))
            if vertical[r, c] == 0:
                legal_moves.append((r, c, 'V'))

    # Step 1: Check for immediate captures
    best_move = None
    max_captures = 0
    for move in legal_moves:
        r, c, d = move
        captures = 0
        if d == 'H':
            affected_boxes = [(r-1, c), (r, c)]
            for br, bc in affected_boxes:
                if 0 <= br < 4 and 0 <= bc < 4:
                    top = horizontal[br, bc]
                    bottom = horizontal[br+1, bc]
                    left = vertical[br, bc]
                    right = vertical[br, bc+1]
                    if (br == r and bc == c):
                        other_edges = [bottom, left, right]
                    elif (br+1 == r and bc == c):
                        other_edges = [top, left, right]
                    else:
                        continue
                    if all(edge != 0 for edge in other_edges) and capture[br, bc] == 0:
                        captures += 1
        else:  # vertical
            affected_boxes = [(r, c-1), (r, c)]
            for br, bc in affected_boxes:
                if 0 <= br < 4 and 0 <= bc < 4:
                    top = horizontal[br, bc]
                    bottom = horizontal[br+1, bc]
                    left = vertical[br, bc]
                    right = vertical[br, bc+1]
                    if (bc == c-1):
                        other_edges = [top, bottom, right]
                    elif (bc == c):
                        other_edges = [top, bottom, left]
                    else:
                        continue
                    if all(edge != 0 for edge in other_edges) and capture[br, bc] == 0:
                        captures += 1
        if captures > max_captures:
            best_move = move
            max_captures = captures
        elif captures == max_captures and captures > 0:
            pass  # prefer earlier moves
    if best_move:
        return f"{best_move[0]},{best_move[1]},{best_move[2]}"

    # Step 2: Block opponent's possible captures
    for move in legal_moves:
        r, c, d = move
        captures = 0
        if d == 'H':
            affected_boxes = [(r-1, c), (r, c)]
            for br, bc in affected_boxes:
                if 0 <= br < 4 and 0 <= bc < 4:
                    top = horizontal[br, bc]
                    bottom = horizontal[br+1, bc]
                    left = vertical[br, bc]
                    right = vertical[br, bc+1]
                    if (br == r and bc == c):
                        other_edges = [bottom, left, right]
                    elif (br+1 == r and bc == c):
                        other_edges = [top, left, right]
                    else:
                        continue
                    if all(edge != 0 for edge in other_edges) and capture[br, bc] == 0:
                        captures += 1
        elif d == 'V':
            affected_boxes = [(r, c-1), (r, c)]
            for br, bc in affected_boxes:
                if 0 <= br < 4 and 0 <= bc < 4:
                    top = horizontal[br, bc]
                    bottom = horizontal[br+1, bc]
                    left = vertical[br, bc]
                    right = vertical[br, bc+1]
                    if (bc == c-1):
                        other_edges = [top, bottom, right]
                    elif (bc == c):
                        other_edges = [top, bottom, left]
                    else:
                        continue
                    if all(edge != 0 for edge in other_edges) and capture[br, bc] == 0:
                        captures += 1
        if captures > 0:
            return f"{r},{c},{d}"

    # Step 3: Avoid creating 3-sided boxes for opponent
    min_risk_moves = []
    other_moves = []
    for move in legal_moves:
        r, c, d = move
        risk_boxes = 0
        if d == 'H':
            for br, bc in [(r-1, c), (r, c)]:
                if 0 <= br < 4 and 0 <= bc < 4:
                    top = horizontal[br, bc]
                    bottom = horizontal[br+1, bc]
                    left = vertical[br, bc]
                    right = vertical[br, bc+1]
                    if br == r and bc == c:  # top
                        filled = 1 + (bottom != 0) + (left != 0) + (right != 0)
                    elif br+1 == r and bc == c:  # bottom
                        filled = 1 + (top != 0) + (left != 0) + (right != 0)
                    else:
                        continue
                    if filled == 3:
                        risk_boxes += 1
        else:  # V
            for br, bc in [(r, c-1), (r, c)]:
                if 0 <= br < 4 and 0 <= bc < 4:
                    top = horizontal[br, bc]
                    bottom = horizontal[br+1, bc]
                    left = vertical[br, bc]
                    right = vertical[br, bc+1]
                    if bc == c-1:  # right
                        filled = 1 + (top != 0) + (bottom != 0) + (left != 0)
                    elif bc == c:  # left
                        filled = 1 + (top != 0) + (bottom != 0) + (right != 0)
                    else:
                        continue
                    if filled == 3:
                        risk_boxes += 1
        if risk_boxes == 0:
            min_risk_moves.append((move, 0))
        else:
            other_moves.append((move, risk_boxes))
    if min_risk_moves:
        return f"{min_risk_moves[0][0][0]},{min_risk_moves[0][0][1]},{min_risk_moves[0][0][2]}"
    else:
        # Sort by lowest risk and choose the first
        other_moves.sort(key=lambda x: x[1])
        return f"{other_moves[0][0][0]},{other_moves[0][0][1]},{other_moves[0][0][2]}"
