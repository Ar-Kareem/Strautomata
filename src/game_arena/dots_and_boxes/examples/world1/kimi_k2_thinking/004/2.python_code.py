
import numpy as np

def _legal_moves(horizontal: np.ndarray, vertical: np.ndarray):
    """Return a list of all legal moves (r,c,dir) for the current board."""
    moves = []
    # horizontal edges: r in 0..4, c in 0..3
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] == 0:
                moves.append((r, c, 'H'))
    # vertical edges: r in 0..3, c in 0..4
    for r in range(4):
        for c in range(5):
            if vertical[r, c] == 0:
                moves.append((r, c, 'V'))
    return moves

def _capture_count(horizontal: np.ndarray, vertical: np.ndarray, move):
    """
    Return the number of boxes (0,1,2) that would be captured by playing `move`.
    The move is assumed to be legal (the edge is currently empty).
    """
    r, c, d = move
    cnt = 0
    if d == 'H':
        # upper box (r-1,c)
        if r > 0:
            if horizontal[r-1, c] != 0 and vertical[r-1, c] != 0 and vertical[r-1, c+1] != 0:
                cnt += 1
        # lower box (r,c)
        if r < 4:
            if horizontal[r+1, c] != 0 and vertical[r, c] != 0 and vertical[r, c+1] != 0:
                cnt += 1
    else:  # 'V'
        # left box (r,c-1)
        if c > 0:
            if horizontal[r, c-1] != 0 and horizontal[r+1, c-1] != 0 and vertical[r, c-1] != 0:
                cnt += 1
        # right box (r,c)
        if c < 4:
            if horizontal[r, c] != 0 and horizontal[r+1, c] != 0 and vertical[r, c+1] != 0:
                cnt += 1
    return cnt

def _max_capture_for_player(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray, player: int):
    """
    Return the maximum number of boxes the given player could capture with a single move
    on the current board.  Player is 1 (us) or -1 (opponent).
    """
    best = 0
    # horizontal edges
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] == 0:
                cap = _capture_count(horizontal, vertical, (r, c, 'H'))
                if cap > best:
                    best = cap
                    if best == 2:
                        return 2
    # vertical edges
    for r in range(4):
        for c in range(5):
            if vertical[r, c] == 0:
                cap = _capture_count(horizontal, vertical, (r, c, 'V'))
                if cap > best:
                    best = cap
                    if best == 2:
                        return 2
    return best

def _apply_move(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray, player: int, move):
    """
    Apply `move` for `player` (1 or -1) and return a tuple
    (new_h, new_v, new_c, captured, capture_cnt).
    `captured` is True iff at least one box was completed.
    `capture_cnt` is the number of boxes captured by this move (0‑2).
    """
    new_h = horizontal.copy()
    new_v = vertical.copy()
    new_c = capture.copy()
    r, c, d = move
    captured = False
    cap_cnt = 0

    if d == 'H':
        new_h[r, c] = player
        # upper box
        if r > 0:
            i, j = r-1, c
            if (new_h[i, j] != 0 and new_h[i+1, j] != 0 and
                new_v[i, j] != 0 and new_v[i, j+1] != 0):
                if new_c[i, j] == 0:
                    new_c[i, j] = player
                    captured = True
                    cap_cnt += 1
        # lower box
        if r < 4:
            i, j = r, c
            if (new_h[i, j] != 0 and new_h[i+1, j] != 0 and
                new_v[i, j] != 0 and new_v[i, j+1] != 0):
                if new_c[i, j] == 0:
                    new_c[i, j] = player
                    captured = True
                    cap_cnt += 1
    else:  # V
        new_v[r, c] = player
        # left box
        if c > 0:
            i, j = r, c-1
            if (new_h[i, j] != 0 and new_h[i+1, j] != 0 and
                new_v[i, j] != 0 and new_v[i, j+1] != 0):
                if new_c[i, j] == 0:
                    new_c[i, j] = player
                    captured = True
                    cap_cnt += 1
        # right box
        if c < 4:
            i, j = r, c
            if (new_h[i, j] != 0 and new_h[i+1, j] != 0 and
                new_v[i, j] != 0 and new_v[i, j+1] != 0):
                if new_c[i, j] == 0:
                    new_c[i, j] = player
                    captured = True
                    cap_cnt += 1

    return new_h, new_v, new_c, captured, cap_cnt

def _format_move(move):
    """Convert a move tuple to the required string representation."""
    r, c, d = move
    return f"{r},{c},{d}"

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Return the next move for the current player (always 1) following the
    greedy‑heuristic described above.
    """
    player = 1

    # ---- 1. Look for a capturing move ---------------------------------
    moves = _legal_moves(horizontal, vertical)
    best_capture_move = None
    best_capture_cnt = 0

    for mv in moves:
        cap = _capture_count(horizontal, vertical, mv)
        if cap > best_capture_cnt:
            best_capture_cnt = cap
            best_capture_move = mv
            if best_capture_cnt == 2:          # cannot do better than 2
                break

    if best_capture_move is not None:
        return _format_move(best_capture_move)

    # ---- 2. No capture – try to find a safe (non‑dangerous) move -------
    best_move = None
    min_opponent_capture = 3   # max possible opponent capture is 2

    for mv in moves:
        # apply the move for the current player (it does not capture)
        new_h, new_v, new_c, _, _ = _apply_move(horizontal, vertical, capture, player, mv)
        # after our move it's the opponent's turn – how many boxes can he capture?
        opp_max = _max_capture_for_player(new_h, new_v, new_c, -player)
        if opp_max < min_opponent_capture:
            min_opponent_capture = opp_max
            best_move = mv
            if opp_max == 0:                 # found a completely safe move
                break

    # At this point we are guaranteed that best_move is not None because
    # the game is not over (policy is called only when a legal move exists).
    return _format_move(best_move)
