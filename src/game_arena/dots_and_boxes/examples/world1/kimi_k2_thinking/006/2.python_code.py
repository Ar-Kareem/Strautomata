
import numpy as np
import time

# -------------------------------------------------------------
# Helper functions for board manipulation
# -------------------------------------------------------------

def get_legal_moves(horiz, vert):
    """Return a list of legal moves as (row, col, dir) tuples."""
    moves = []
    # Horizontal edges: rows 0..4, cols 0..3
    for r in range(5):
        for c in range(4):
            if horiz[r, c] == 0:
                moves.append((r, c, 'H'))
    # Vertical edges: rows 0..3, cols 0..4
    for r in range(4):
        for c in range(5):
            if vert[r, c] == 0:
                moves.append((r, c, 'V'))
    return moves

def count_captures(horiz, vert, cap, player, row, col, dire):
    """How many boxes would be captured by drawing this edge?"""
    captured = 0
    if dire == 'H':
        # box above
        if row > 0:
            i, j = row - 1, col
            if cap[i, j] == 0:
                if horiz[i, j] != 0 and vert[i, j] != 0 and vert[i, j + 1] != 0:
                    captured += 1
        # box below
        if row < 4:
            i, j = row, col
            if cap[i, j] == 0:
                if horiz[i + 1, j] != 0 and vert[i, j] != 0 and vert[i, j + 1] != 0:
                    captured += 1
    else:  # 'V'
        # box to the left
        if col > 0:
            i, j = row, col - 1
            if cap[i, j] == 0:
                if horiz[i, j] != 0 and horiz[i + 1, j] != 0 and vert[i, j] != 0:
                    captured += 1
        # box to the right
        if col < 4:
            i, j = row, col
            if cap[i, j] == 0:
                if horiz[i, j] != 0 and horiz[i + 1, j] != 0 and vert[i, j + 1] != 0:
                    captured += 1
    return captured

def get_captured_boxes(horiz, vert, cap, player, row, col, dire):
    """Return a list of (i,j) boxes that would be captured by this move."""
    boxes = []
    if dire == 'H':
        if row > 0:
            i, j = row - 1, col
            if cap[i, j] == 0:
                if horiz[i, j] != 0 and vert[i, j] != 0 and vert[i, j + 1] != 0:
                    boxes.append((i, j))
        if row < 4:
            i, j = row, col
            if cap[i, j] == 0:
                if horiz[i + 1, j] != 0 and vert[i, j] != 0 and vert[i, j + 1] != 0:
                    boxes.append((i, j))
    else:  # 'V'
        if col > 0:
            i, j = row, col - 1
            if cap[i, j] == 0:
                if horiz[i, j] != 0 and horiz[i + 1, j] != 0 and vert[i, j] != 0:
                    boxes.append((i, j))
        if col < 4:
            i, j = row, col
            if cap[i, j] == 0:
                if horiz[i, j] != 0 and horiz[i + 1, j] != 0 and vert[i, j + 1] != 0:
                    boxes.append((i, j))
    return boxes

def count_threats(horiz, vert, cap, player, row, col, dire):
    """How many unclaimed boxes would have exactly three sides after this move?"""
    threats = 0
    if dire == 'H':
        # box above
        if row > 0:
            i, j = row - 1, col
            if cap[i, j] == 0:
                cnt = (horiz[i, j] != 0) + (horiz[i + 1, j] != 0) + (vert[i, j] != 0) + (vert[i, j + 1] != 0)
                if cnt == 2:  # after drawing the new edge it becomes 3
                    threats += 1
        # box below
        if row < 4:
            i, j = row, col
            if cap[i, j] == 0:
                cnt = (horiz[i, j] != 0) + (horiz[i + 1, j] != 0) + (vert[i, j] != 0) + (vert[i, j + 1] != 0)
                if cnt == 2:
                    threats += 1
    else:  # 'V'
        # box left
        if col > 0:
            i, j = row, col - 1
            if cap[i, j] == 0:
                cnt = (horiz[i, j] != 0) + (horiz[i + 1, j] != 0) + (vert[i, j] != 0) + (vert[i, j + 1] != 0)
                if cnt == 2:
                    threats += 1
        # box right
        if col < 4:
            i, j = row, col
            if cap[i, j] == 0:
                cnt = (horiz[i, j] != 0) + (horiz[i + 1, j] != 0) + (vert[i, j] != 0) + (vert[i, j + 1] != 0)
                if cnt == 2:
                    threats += 1
    return threats

def apply_move(horiz, vert, cap, player, row, col, dire):
    """Return new board state after playing the given edge."""
    new_h = horiz.copy()
    new_v = vert.copy()
    new_c = cap.copy()
    if dire == 'H':
        new_h[row, col] = player
    else:
        new_v[row, col] = player
    boxes = get_captured_boxes(horiz, vert, cap, player, row, col, dire)
    captured = len(boxes)
    for i, j in boxes:
        new_c[i, j] = player
    return new_h, new_v, new_c, captured

def heuristic_eval(horiz, vert, cap, player):
    """Static evaluation from the point of view of the player to move."""
    # difference in captured boxes (positive = us ahead)
    score = np.sum(cap)
    # immediate capture potential for the player
    best_capture = 0
    for move in get_legal_moves(horiz, vert):
        r, c, d = move
        cap_cnt = count_captures(horiz, vert, cap, player, r, c, d)
        if cap_cnt > best_capture:
            best_capture = cap_cnt
    # weight the potential capture a bit less than a sure box
    w = 0.8
    score += player * best_capture * w
    return score

def minimax(horiz, vert, cap, player, depth, alpha, beta):
    """Alpha‑beta search. Returns (best_move, value)."""
    moves = get_legal_moves(horiz, vert)
    if not moves or depth == 0:
        return None, heuristic_eval(horiz, vert, cap, player)

    # ----- move ordering -----
    scored = []
    for mv in moves:
        r, c, d = mv
        captures = count_captures(horiz, vert, cap, player, r, c, d)
        threats = count_threats(horiz, vert, cap, player, r, c, d)
        if captures > 0:
            score = 1000 + captures * 100 - threats
        else:
            score = -threats
        scored.append((score, mv))
    scored.sort(key=lambda x: x[0], reverse=True)
    ordered_moves = [m for _, m in scored]

    if player == 1:   # maximizing
        best_val = -float('inf')
        best_move = None
        for mv in ordered_moves:
            r, c, d = mv
            nh, nv, nc, captured = apply_move(horiz, vert, cap, player, r, c, d)
            nxt_player = player if captured > 0 else -player
            _, val = minimax(nh, nv, nc, nxt_player, depth - 1, alpha, beta)
            if val > best_val:
                best_val = val
                best_move = mv
            alpha = max(alpha, best_val)
            if beta <= alpha:
                break
        return best_move, best_val
    else:             # minimizing
        best_val = float('inf')
        best_move = None
        for mv in ordered_moves:
            r, c, d = mv
            nh, nv, nc, captured = apply_move(horiz, vert, cap, player, r, c, d)
            nxt_player = player if captured > 0 else -player
            _, val = minimax(nh, nv, nc, nxt_player, depth - 1, alpha, beta)
            if val < best_val:
                best_val = val
                best_move = mv
            beta = min(beta, best_val)
            if beta <= alpha:
                break
        return best_move, best_val

def fallback_move(horiz, vert, cap):
    """Pick a move when search fails: captures > safe > minimal gifts."""
    moves = get_legal_moves(horiz, vert)
    best = None
    best_score = -float('inf')
    for mv in moves:
        r, c, d = mv
        captures = count_captures(horiz, vert, cap, 1, r, c, d)
        threats = count_threats(horiz, vert, cap, 1, r, c, d)
        if captures > 0:
            score = 1000 + captures * 100 - threats
        else:
            score = -threats
        if score > best_score:
            best_score = score
            best = mv
    if best is None:
        best = moves[0] if moves else (0, 0, 'H')
    return best

def policy(horizontal, vertical, capture):
    """
    Return a legal move string ``row,col,dir`` for the current player.
    The algorithm performs an iterative‑deepening alpha‑beta search with
    heuristics based on captured boxes and immediate capture potential.
    """
    start = time.time()
    # quick exit for single move
    moves = get_legal_moves(horizontal, vertical)
    if len(moves) == 1:
        r, c, d = moves[0]
        return f"{r},{c},{d}"

    best_move = fallback_move(horizontal, vertical, capture)
    depth = 1
    while True:
        if time.time() - start > 0.9:
            break
        try:
            move, _ = minimax(horizontal, vertical, capture, player=1,
                              depth=depth, alpha=-float('inf'), beta=float('inf'))
        except Exception:
            # safety – exit on any unexpected error
            break
        if move is not None:
            best_move = move
        depth += 1
        if depth > 20:          # safety cap
            break

    r, c, d = best_move
    return f"{r},{c},{d}"
