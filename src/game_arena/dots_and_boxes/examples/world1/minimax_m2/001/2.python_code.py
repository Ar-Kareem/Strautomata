
import numpy as np

def count_edges(box_i, box_j, horizontal, vertical):
    count = 0
    if box_i < 0 or box_i > 3 or box_j < 0 or box_j > 3:
        return 0
    if horizontal[box_i, box_j] != 0:
        count += 1
    if horizontal[box_i+1, box_j] != 0:
        count += 1
    if vertical[box_i, box_j] != 0:
        count += 1
    if vertical[box_i, box_j+1] != 0:
        count += 1
    return count

def would_capture_boxes(move, horizontal, vertical):
    i, j, dir = move
    captured = []
    if dir == 'H':
        if 0 <= i < 4 and 0 <= j < 4:
            if horizontal[i+1, j] != 0 and vertical[i, j] != 0 and vertical[i, j+1] != 0:
                captured.append((i, j))
        if i >= 1 and 0 <= j < 4:
            if horizontal[i-1, j] != 0 and vertical[i-1, j] != 0 and vertical[i-1, j+1] != 0:
                captured.append((i-1, j))
    else:
        if 0 <= i < 4 and 0 <= j < 4:
            if horizontal[i, j] != 0 and horizontal[i+1, j] != 0 and vertical[i, j+1] != 0:
                captured.append((i, j))
        if 0 <= i < 4 and j >= 1:
            if horizontal[i, j-1] != 0 and horizontal[i+1, j-1] != 0 and vertical[i, j-1] != 0:
                captured.append((i, j-1))
    return captured

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    legal_moves = []
    for i in range(5):
        for j in range(5):
            if horizontal[i, j] == 0:
                legal_moves.append((i, j, 'H'))
    for i in range(5):
        for j in range(5):
            if vertical[i, j] == 0:
                legal_moves.append((i, j, 'V'))

    capturing_moves = []
    for move in legal_moves:
        captured = would_capture_boxes(move, horizontal, vertical)
        if captured:
            capturing_moves.append((move, len(captured)))
    
    if capturing_moves:
        best = max(capturing_moves, key=lambda x: x[1])
        move = best[0]
        return f"{move[0]},{move[1]},{move[2]}"

    safe_moves = []
    for move in legal_moves:
        i, j, dir = move
        unsafe = False
        if dir == 'H':
            if 0 <= i < 4 and 0 <= j < 4:
                count = count_edges(i, j, horizontal, vertical) + 1
                if count == 3:
                    unsafe = True
            if i >= 1 and 0 <= j < 4:
                count = count_edges(i-1, j, horizontal, vertical) + 1
                if count == 3:
                    unsafe = True
        else:
            if 0 <= i < 4 and 0 <= j < 4:
                count = count_edges(i, j, horizontal, vertical) + 1
                if count == 3:
                    unsafe = True
            if 0 <= i < 4 and j >= 1:
                count = count_edges(i, j-1, horizontal, vertical) + 1
                if count == 3:
                    unsafe = True

        if not unsafe:
            safe_moves.append(move)

    if safe_moves:
        move = safe_moves[0]
        return f"{move[0]},{move[1]},{move[2]}"

    move = legal_moves[0]
    return f"{move[0]},{move[1]},{move[2]}"
