
import time

# ------------------------- precomputed line tables -------------------------
def _build_lines():
    lines, seen = [], set()
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx == 0 and dy == 0 and dz == 0:
                    continue
                # keep exactly one direction from each opposite pair
                if dx < 0 or (dx == 0 and dy < 0) or (dx == 0 and dy == 0 and dz < 0):
                    continue
                for x in range(3):
                    for y in range(3):
                        for z in range(3):
                            pts = []
                            ok = True
                            for t in range(3):
                                nx, ny, nz = x + t * dx, y + t * dy, z + t * dz
                                if not (0 <= nx < 3 and 0 <= ny < 3 and 0 <= nz < 3):
                                    ok = False
                                    break
                                pts.append(nx * 9 + ny * 3 + nz)
                            if ok:
                                pts = tuple(pts)
                                if pts not in seen:
                                    seen.add(pts)
                                    lines.append(pts)
    return lines


LINES = _build_lines()                       # all 49 winning lines (flat indices)
CELL_LINES = [[] for _ in range(27)]
for _line in LINES:
    for _idx in _line:
        CELL_LINES[_idx].append(_line)

ORDER = sorted(range(27), key=lambda i: len(CELL_LINES[i]), reverse=True)

# line-strength weights: [none, one-stone, two-open, completed]
W = (0, 5, 50, 10 ** 6)
WIN = 10 ** 6
INF = float("inf")
TIME_LIMIT = 0.8
DEPTH_CAP = 12


class _Timeout(Exception):
    pass


_nodes = 0


def _evaluate(flat, p):
    """Score the position from the perspective of player p (+1 or -1)."""
    q = -p
    score = 0
    for a, b, c in LINES:
        m = (flat[a] == p) + (flat[b] == p) + (flat[c] == p)
        o = (flat[a] == q) + (flat[b] == q) + (flat[c] == q)
        if m and not o:
            score += W[m]
        elif o and not m:
            score -= W[o]
    return score


def _won_line(flat, idx, p):
    """True if a line through cell idx is fully occupied by player p."""
    for a, b, c in CELL_LINES[idx]:
        if flat[a] == p and flat[b] == p and flat[c] == p:
            return True
    return False


def _negamax(flat, p, depth, alpha, beta, deadline):
    global _nodes
    _nodes += 1
    if _nodes % 512 == 0 and time.time() > deadline:
        raise _Timeout()
    if depth == 0:
        return _evaluate(flat, p)
    best = -INF
    found = False
    for idx in ORDER:
        if flat[idx] != 0:
            continue
        found = True
        flat[idx] = p
        if _won_line(flat, idx, p):
            val = WIN + depth  # forced win (sooner is better)
        else:
            val = -_negamax(flat, -p, depth - 1, -beta, -alpha, deadline)
        flat[idx] = 0
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    if not found:
        return _evaluate(flat, p)  # board full
    return best


def _root_search(flat, depth, deadline):
    p = 1
    alpha = -INF
    best_val, best_idx = -INF, None
    for idx in ORDER:
        if flat[idx] != 0:
            continue
        flat[idx] = p
        if _won_line(flat, idx, p):
            val = WIN + depth
        else:
            val = -_negamax(flat, -p, depth - 1, -INF, -alpha, deadline)
        flat[idx] = 0
        if val > best_val:
            best_val, best_idx = val, idx
        if val > alpha:
            alpha = val
    return best_val, best_idx


def policy(board):
    try:
        flat = []
        for i in range(3):
            for j in range(3):
                flat.extend(board[i][j])
        empties = [i for i in ORDER if flat[i] == 0]

        def _coord(idx):
            return (idx // 9, (idx // 3) % 3, idx % 3)

        if not empties:
            return (0, 0, 0)

        me, opp = 1, -1

        # 1) take an immediate win
        for idx in empties:
            flat[idx] = me
            if _won_line(flat, idx, me):
                flat[idx] = 0
                return _coord(idx)
            flat[idx] = 0

        # 2) block opponent's immediate win
        threat = None
        for idx in empties:
            flat[idx] = opp
            if _won_line(flat, idx, opp):
                threat = idx
                flat[idx] = 0
                break
            flat[idx] = 0
        if threat is not None:
            return _coord(threat)

        # 3) iterative-deepening alpha-beta negamax within a time budget
        global _nodes
        _nodes = 0
        deadline = time.time() + TIME_LIMIT
        best_move = empties[0]
        depth = 1
        try:
            while depth <= DEPTH_CAP and depth <= len(empties):
                val, mv = _root_search(flat, depth, deadline)
                best_move = mv
                if val >= WIN:
                    break
                depth += 1
        except _Timeout:
            pass
        return _coord(best_move)
    except Exception:
        # absolute safety fallback: first empty cell
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    if board[i][j][k] == 0:
                        return (i, j, k)
        return (0, 0, 0)
