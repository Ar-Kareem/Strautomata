
import numpy as np
import time

TERMINAL_SCALE = 100000
SCORE_SCALE = 1000
THREE_BOX_BONUS = 800
SAFE_MOVE_BONUS = 10
NEG_INF = -10**30
POS_INF = 10**30

_ALPHA_START = 0.0
_ALPHA_TIME_LIMIT = 0.8
_ALPHA_NODES = 0


class Timeout(Exception):
    pass


def _check_time():
    global _ALPHA_NODES
    _ALPHA_NODES += 1
    if (_ALPHA_NODES & 63) == 0:
        if time.monotonic() - _ALPHA_START > _ALPHA_TIME_LIMIT:
            raise Timeout()


def _score_diff(c, player):
    boxes = c[:4, :4]
    my = int(np.count_nonzero(boxes == player))
    opp = int(np.count_nonzero(boxes == -player))
    return my - opp


def _legal_moves(h, v, c):
    moves = []
    # horizontal edges: rows 0..4, columns 0..3
    for r in range(5):
        for col in range(4):
            if h[r, col] == 0:
                moves.append((r, col, 'H'))
    # vertical edges: rows 0..3, columns 0..4
    for r in range(4):
        for col in range(5):
            if v[r, col] == 0:
                moves.append((r, col, 'V'))
    return moves


def _box_sides_grid(h, v):
    sides = [[0, 0, 0, 0] for _ in range(4)]
    for br in range(4):
        row = sides[br]
        for bc in range(4):
            s = 0
            if h[br, bc] != 0:
                s += 1
            if h[br + 1, bc] != 0:
                s += 1
            if v[br, bc] != 0:
                s += 1
            if v[br, bc + 1] != 0:
                s += 1
            row[bc] = s
    return sides


def _move_metrics_with_sides(c, sides, r, col, direction):
    cap = 0
    unsafe = 0
    adj = 0

    if direction == 'H':
        if r > 0:
            br = r - 1
            bc = col
            if c[br, bc] == 0:
                adj += 1
                s = sides[br][bc] + 1
                if s == 4:
                    cap += 1
                elif s == 3:
                    unsafe += 1
        if r < 4:
            br = r
            bc = col
            if c[br, bc] == 0:
                adj += 1
                s = sides[br][bc] + 1
                if s == 4:
                    cap += 1
                elif s == 3:
                    unsafe += 1
    else:  # 'V'
        if col > 0:
            br = r
            bc = col - 1
            if c[br, bc] == 0:
                adj += 1
                s = sides[br][bc] + 1
                if s == 4:
                    cap += 1
                elif s == 3:
                    unsafe += 1
        if col < 4:
            br = r
            bc = col
            if c[br, bc] == 0:
                adj += 1
                s = sides[br][bc] + 1
                if s == 4:
                    cap += 1
                elif s == 3:
                    unsafe += 1

    if cap > 0:
        unsafe = 0
    return cap, unsafe, adj


def _order_moves(h, v, c, moves):
    sides = _box_sides_grid(h, v)
    infos = []
    for move in moves:
        r, col, direction = move
        cap, unsafe, adj = _move_metrics_with_sides(c, sides, r, col, direction)
        if cap > 0:
            priority = 0
        elif unsafe == 0:
            priority = 1
        else:
            priority = 2
        center_dist = abs(r - 2) + abs(col - 2)
        key = (priority, -cap, unsafe, -adj, center_dist)
        infos.append((key, move))
    infos.sort(key=lambda x: x[0])
    return infos


def _apply_move(h, v, c, r, col, direction, player):
    h2 = h.copy()
    v2 = v.copy()
    c2 = c.copy()
    captured = 0

    if direction == 'H':
        h2[r, col] = player
        if r > 0:
            br = r - 1
            bc = col
            if c2[br, bc] == 0 and h2[br, bc] != 0 and h2[r, col] != 0 and v2[br, bc] != 0 and v2[br, bc + 1] != 0:
                c2[br, bc] = player
                captured += 1
        if r < 4:
            br = r
            bc = col
            if c2[br, bc] == 0 and h2[r, col] != 0 and h2[r + 1, bc] != 0 and v2[br, bc] != 0 and v2[br, bc + 1] != 0:
                c2[br, bc] = player
                captured += 1
    else:  # 'V'
        v2[r, col] = player
        if col > 0:
            br = r
            bc = col - 1
            if c2[br, bc] == 0 and h2[br, bc] != 0 and h2[br + 1, bc] != 0 and v2[br, bc] != 0 and v2[r, col] != 0:
                c2[br, bc] = player
                captured += 1
        if col < 4:
            br = r
            bc = col
            if c2[br, bc] == 0 and h2[br, bc] != 0 and h2[br + 1, bc] != 0 and v2[r, col] != 0 and v2[br, bc + 1] != 0:
                c2[br, bc] = player
                captured += 1

    next_player = player if captured > 0 else -player
    return h2, v2, c2, next_player, captured


def _evaluate(h, v, c, player):
    total_boxes = int(np.count_nonzero(c[:4, :4] != 0))
    if total_boxes == 16:
        return TERMINAL_SCALE * _score_diff(c, player)

    sides = _box_sides_grid(h, v)

    three_count = 0
    for br in range(4):
        for bc in range(4):
            if c[br, bc] == 0 and sides[br][bc] == 3:
                three_count += 1

    safe_moves = 0
    for r in range(5):
        for col in range(4):
            if h[r, col] == 0:
                cap, unsafe, _ = _move_metrics_with_sides(c, sides, r, col, 'H')
                if cap == 0 and unsafe == 0:
                    safe_moves += 1
    for r in range(4):
        for col in range(5):
            if v[r, col] == 0:
                cap, unsafe, _ = _move_metrics_with_sides(c, sides, r, col, 'V')
                if cap == 0 and unsafe == 0:
                    safe_moves += 1

    diff = _score_diff(c, player)
    return SCORE_SCALE * diff + THREE_BOX_BONUS * three_count + SAFE_MOVE_BONUS * safe_moves


def _alpha_beta(h, v, c, player, depth, alpha, beta):
    _check_time()

    if depth <= 0:
        return _evaluate(h, v, c, player)

    moves = _legal_moves(h, v, c)
    if not moves:
        return TERMINAL_SCALE * _score_diff(c, player)

    ordered = _order_moves(h, v, c, moves)
    best = NEG_INF

    for _, move in ordered:
        r, col, direction = move
        h2, v2, c2, next_player, _ = _apply_move(h, v, c, r, col, direction, player)

        if next_player == player:
            val = _alpha_beta(h2, v2, c2, player, depth - 1, alpha, beta)
        else:
            val = -_alpha_beta(h2, v2, c2, -player, depth - 1, -beta, -alpha)

        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    return best


def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    global _ALPHA_START, _ALPHA_TIME_LIMIT, _ALPHA_NODES

    h = np.array(horizontal, dtype=np.int8)
    v = np.array(vertical, dtype=np.int8)
    c = np.array(capture, dtype=np.int8)

    player = 1  # we are always player 1 in this API
    moves = _legal_moves(h, v, c)
    if not moves:
        return "0,0,H"

    _ALPHA_START = time.monotonic()
    _ALPHA_TIME_LIMIT = 0.8
    _ALPHA_NODES = 0

    ordered = _order_moves(h, v, c, moves)
    best_move = ordered[0][1]
    best_val = NEG_INF

    for depth in range(1, 41):
        depth_ordered = list(ordered)
        if best_move is not None:
            # try previous best move first for better pruning
            depth_ordered.sort(key=lambda x: 0 if x[1] == best_move else 1)

        current_best = None
        current_val = NEG_INF
        alpha = NEG_INF
        beta = POS_INF

        try:
            for _, move in depth_ordered:
                r, col, direction = move
                h2, v2, c2, next_player, _ = _apply_move(h, v, c, r, col, direction, player)

                if next_player == player:
                    val = _alpha_beta(h2, v2, c2, player, depth - 1, alpha, beta)
                else:
                    val = -_alpha_beta(h2, v2, c2, -player, depth - 1, -beta, -alpha)

                if val > current_val:
                    current_val = val
                    current_best = move
                if current_val > alpha:
                    alpha = current_val
                if alpha >= beta:
                    break
        except Timeout:
            break

        if current_best is not None:
            best_move = current_best
            best_val = current_val

    return f"{best_move[0]},{best_move[1]},{best_move[2]}"
