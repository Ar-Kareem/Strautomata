
import numpy as np

# 4x4 boxes -> valid edges:
# Horizontal: rows 0..4, cols 0..3
# Vertical:   rows 0..3, cols 0..4

def _valid_moves(horizontal, vertical):
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

def _adjacent_boxes(move):
    r, c, d = move
    boxes = []
    if d == 'H':
        # box above
        if r > 0 and c < 4:
            boxes.append((r - 1, c))
        # box below
        if r < 4 and c < 4:
            boxes.append((r, c))
    else:  # 'V'
        # box left
        if c > 0 and r < 4:
            boxes.append((r, c - 1))
        # box right
        if c < 4 and r < 4:
            boxes.append((r, c))
    return boxes

def _box_sides(horizontal, vertical, br, bc):
    # box at (br, bc), 0<=br,bc<4
    s = 0
    if horizontal[br, bc] != 0:
        s += 1
    if horizontal[br + 1, bc] != 0:
        s += 1
    if vertical[br, bc] != 0:
        s += 1
    if vertical[br, bc + 1] != 0:
        s += 1
    return s

def _captures_for_move(horizontal, vertical, capture, move):
    count = 0
    for br, bc in _adjacent_boxes(move):
        if capture[br, bc] == 0 and _box_sides(horizontal, vertical, br, bc) == 3:
            count += 1
    return count

def _apply_move(horizontal, vertical, capture, move, player):
    h = horizontal.copy()
    v = vertical.copy()
    cap = capture.copy()

    r, c, d = move
    if d == 'H':
        h[r, c] = player
    else:
        v[r, c] = player

    gained = 0
    for br, bc in _adjacent_boxes(move):
        if cap[br, bc] == 0 and _box_sides(h, v, br, bc) == 4:
            cap[br, bc] = player
            gained += 1

    return h, v, cap, gained

def _is_safe_move(horizontal, vertical, capture, move):
    # Safe means after making the move, no adjacent unclaimed box has exactly 3 sides.
    # Equivalently, before the move, no adjacent unclaimed box has 2 sides.
    # Capturing moves are treated separately and are not "safe" by this function.
    if _captures_for_move(horizontal, vertical, capture, move) > 0:
        return False

    for br, bc in _adjacent_boxes(move):
        if capture[br, bc] == 0:
            if _box_sides(horizontal, vertical, br, bc) == 2:
                return False
    return True

def _move_risk_score(horizontal, vertical, capture, move):
    # Lower is better.
    # Penalize creating 3-sided boxes; mild preference for boundary / low-side areas.
    r, c, d = move
    score = 0.0

    for br, bc in _adjacent_boxes(move):
        if capture[br, bc] != 0:
            continue
        sides = _box_sides(horizontal, vertical, br, bc)
        after = sides + 1
        if after == 3:
            score += 100.0
        elif after == 2:
            score += 8.0
        elif after == 1:
            score += 2.0

    # Slight boundary preference as tie-breaker
    if d == 'H':
        if r == 0 or r == 4:
            score -= 0.5
    else:
        if c == 0 or c == 4:
            score -= 0.5

    return score

def _forced_capture_rollout(horizontal, vertical, capture, player):
    # Simulate only forced capture continuation for current player.
    # At each step, take the move with maximum immediate captures.
    # Returns total boxes captured in this rollout.
    total = 0
    h, v, cap = horizontal, vertical, capture

    while True:
        moves = _valid_moves(h, v)
        best_move = None
        best_gain = 0
        for mv in moves:
            g = _captures_for_move(h, v, cap, mv)
            if g > best_gain:
                best_gain = g
                best_move = mv
        if best_move is None or best_gain == 0:
            break
        h, v, cap, gained = _apply_move(h, v, cap, best_move, player)
        total += gained

    return total

def _opponent_damage_if_play(horizontal, vertical, capture, move):
    # Simulate our move; if we do not capture, estimate the opponent's forced scoring run.
    h, v, cap, gained = _apply_move(horizontal, vertical, capture, move, 1)
    if gained > 0:
        return -gained  # beneficial now
    return _forced_capture_rollout(h, v, cap, -1)

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    moves = _valid_moves(horizontal, vertical)

    # Absolute fallback: should only happen on terminal boards.
    if not moves:
        return "0,0,H"

    # 1) Immediate captures first.
    capture_moves = []
    best_cap = 0
    for mv in moves:
        g = _captures_for_move(horizontal, vertical, capture, mv)
        if g > 0:
            if g > best_cap:
                best_cap = g
                capture_moves = [mv]
            elif g == best_cap:
                capture_moves.append(mv)

    if capture_moves:
        # Tie-break: prefer move that keeps giving us continued capture opportunities
        best_mv = capture_moves[0]
        best_score = -10**9
        for mv in capture_moves:
            h, v, cap, gained = _apply_move(horizontal, vertical, capture, mv, 1)
            cont = _forced_capture_rollout(h, v, cap, 1)
            # Immediate gain dominates; continuation breaks ties
            score = 1000 * gained + cont - _move_risk_score(horizontal, vertical, capture, mv)
            if score > best_score:
                best_score = score
                best_mv = mv
        return f"{best_mv[0]},{best_mv[1]},{best_mv[2]}"

    # 2) Safe moves.
    safe_moves = [mv for mv in moves if _is_safe_move(horizontal, vertical, capture, mv)]
    if safe_moves:
        best_mv = safe_moves[0]
        best_score = 10**9
        for mv in safe_moves:
            score = _move_risk_score(horizontal, vertical, capture, mv)

            # Prefer moves adjacent to boxes with fewer sides already drawn.
            local = 0.0
            for br, bc in _adjacent_boxes(mv):
                if capture[br, bc] == 0:
                    local += _box_sides(horizontal, vertical, br, bc)
            score += 0.2 * local

            if score < best_score:
                best_score = score
                best_mv = mv
        return f"{best_mv[0]},{best_mv[1]},{best_mv[2]}"

    # 3) No safe moves: minimize likely opponent haul.
    best_mv = moves[0]
    best_score = 10**9
    for mv in moves:
        damage = _opponent_damage_if_play(horizontal, vertical, capture, mv)
        risk = _move_risk_score(horizontal, vertical, capture, mv)

        # Number of newly-created 3-sided boxes
        created_threes = 0
        for br, bc in _adjacent_boxes(mv):
            if capture[br, bc] == 0 and _box_sides(horizontal, vertical, br, bc) == 2:
                created_threes += 1

        score = 1000 * damage + 50 * created_threes + risk
        if score < best_score:
            best_score = score
            best_mv = mv

    return f"{best_mv[0]},{best_mv[1]},{best_mv[2]}"
