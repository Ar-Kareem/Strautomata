
import time
import numpy as np

# Precomputed constants for 4x4 box grid (5x5 dots)
# Boxes: 0..15 (row = b // 4, col = b % 4)
# Horizontal edges: 0..19 (r in 0..4, c in 0..3 -> r * 4 + c)
# Vertical edges: 20..39 (r in 0..3, c in 0..4 -> 20 + r * 5 + c)

BOX_MASK_H = [0] * 16
BOX_MASK_V = [0] * 16
BOX_EDGES = [[] for _ in range(16)]
EDGE_BOXES = [[] for _ in range(40)]
EDGE_TO_STR = ["" for _ in range(40)]
BOX_NEIGHBORS = [[] for _ in range(16)]

for b in range(16):
    r, c = b // 4, b % 4
    top_h = r * 4 + c
    bot_h = (r + 1) * 4 + c
    left_v = r * 5 + c
    right_v = r * 5 + (c + 1)
    
    BOX_MASK_H[b] = (1 << top_h) | (1 << bot_h)
    BOX_MASK_V[b] = (1 << left_v) | (1 << right_v)
    BOX_EDGES[b] = [top_h, bot_h, 20 + left_v, 20 + right_v]
    
    if r > 0:
        BOX_NEIGHBORS[b].append((r - 1) * 4 + c)
    if r < 3:
        BOX_NEIGHBORS[b].append((r + 1) * 4 + c)
    if c > 0:
        BOX_NEIGHBORS[b].append(r * 4 + (c - 1))
    if c < 3:
        BOX_NEIGHBORS[b].append(r * 4 + (c + 1))

for e in range(20):
    r, c = e // 4, e % 4
    EDGE_TO_STR[e] = f"{r},{c},H"
    if r > 0:
        EDGE_BOXES[e].append((r - 1) * 4 + c)
    if r < 4:
        EDGE_BOXES[e].append(r * 4 + c)

for e in range(20):
    r, c = e // 5, e % 5
    edge_id = 20 + e
    EDGE_TO_STR[edge_id] = f"{r},{c},V"
    if c > 0:
        EDGE_BOXES[edge_id].append(r * 4 + (c - 1))
    if c < 4:
        EDGE_BOXES[edge_id].append(r * 4 + c)


def _get_sacrifice_chain_length(edge: int, H: int, V: int) -> int:
    """Fast simulation of greedy captures conceded by playing a sacrifice edge."""
    if edge < 20:
        cur_H = H | (1 << edge)
        cur_V = V
    else:
        cur_H = H
        cur_V = V | (1 << (edge - 20))
    
    chain_boxes = 0
    while True:
        found = False
        for b in range(16):
            sides = (cur_H & BOX_MASK_H[b]).bit_count() + (cur_V & BOX_MASK_V[b]).bit_count()
            if sides == 3:
                for e in BOX_EDGES[b]:
                    if e < 20:
                        if not (cur_H & (1 << e)):
                            cur_H |= (1 << e)
                            chain_boxes += 1
                            found = True
                            break
                    else:
                        v_idx = e - 20
                        if not (cur_V & (1 << v_idx)):
                            cur_V |= (1 << v_idx)
                            chain_boxes += 1
                            found = True
                            break
                if found:
                    break
        if not found:
            break
    return chain_boxes


def _get_best_heuristic_move(H: int, V: int) -> int:
    """Instant heuristic move selection used as base/fallback before search."""
    captures_list = []
    safe_list = []
    sacrifices_list = []
    
    for e in range(40):
        if e < 20:
            if H & (1 << e):
                continue
        else:
            if V & (1 << (e - 20)):
                continue
        
        c, t = 0, 0
        for b in EDGE_BOXES[e]:
            s = (H & BOX_MASK_H[b]).bit_count() + (V & BOX_MASK_V[b]).bit_count()
            if s == 3:
                c += 1
            elif s == 2:
                t += 1
        if c > 0:
            captures_list.append((c, e))
        elif t == 0:
            safe_list.append(e)
        else:
            sacrifices_list.append(e)
            
    if captures_list:
        captures_list.sort(key=lambda x: x[0], reverse=True)
        return captures_list[0][1]
        
    if safe_list:
        scored_safe = []
        for e in safe_list:
            twos = 0
            for b in EDGE_BOXES[e]:
                s = (H & BOX_MASK_H[b]).bit_count() + (V & BOX_MASK_V[b]).bit_count()
                if s == 1:
                    twos += 1
            is_perim = len(EDGE_BOXES[e]) == 1
            scored_safe.append((twos, not is_perim, e))
        scored_safe.sort()
        return scored_safe[0][2]
        
    if sacrifices_list:
        sac_scored = []
        for e in sacrifices_list:
            ch = _get_sacrifice_chain_length(e, H, V)
            sac_scored.append((ch, e))
        sac_scored.sort()
        return sac_scored[0][1]
        
    return None


def _negamax(H: int, V: int, depth: int, alpha: int, beta: int,
             start_time: float, max_time: float, tt: dict, node_counter: list):
    node_counter[0] += 1
    if (node_counter[0] & 255) == 0 and (time.time() - start_time) > max_time:
        raise TimeoutError()

    if H == 0xFFFFF and V == 0xFFFFF:
        return 0, None

    state_key = (H, V)
    if state_key in tt:
        entry_depth, entry_flag, entry_val, entry_move = tt[state_key]
        if entry_depth >= depth:
            if entry_flag == 0:  # EXACT
                return entry_val, entry_move
            elif entry_flag == 1:  # LOWERBOUND
                alpha = max(alpha, entry_val)
            elif entry_flag == 2:  # UPPERBOUND
                beta = min(beta, entry_val)
            if alpha >= beta:
                return entry_val, entry_move

    captures_list = []
    safe_list = []
    sacrifices_list = []

    for e in range(40):
        if e < 20:
            if H & (1 << e):
                continue
        else:
            if V & (1 << (e - 20)):
                continue

        c, t = 0, 0
        for b in EDGE_BOXES[e]:
            s = (H & BOX_MASK_H[b]).bit_count() + (V & BOX_MASK_V[b]).bit_count()
            if s == 3:
                c += 1
            elif s == 2:
                t += 1
        if c > 0:
            captures_list.append((e, c))
        elif t == 0:
            safe_list.append(e)
        else:
            sacrifices_list.append(e)

    empty_count = 40 - H.bit_count() - V.bit_count()

    if captures_list:
        captures_list.sort(key=lambda x: x[1], reverse=True)
        moves = [e for e, _ in captures_list]

        # Consider double-cross if no safe moves left and non-trivial board remains
        if not safe_list and empty_count > 4:
            for e in sacrifices_list:
                is_dc = False
                for b in EDGE_BOXES[e]:
                    s = (H & BOX_MASK_H[b]).bit_count() + (V & BOX_MASK_V[b]).bit_count()
                    if s == 2:
                        for nb in BOX_NEIGHBORS[b]:
                            nb_s = (H & BOX_MASK_H[nb]).bit_count() + (V & BOX_MASK_V[nb]).bit_count()
                            if nb_s == 3:
                                is_dc = True
                                break
                if is_dc:
                    moves.append(e)
                    break
    elif safe_list:
        if depth <= 0:
            parity = 1 if (len(safe_list) % 2 == 1) else -1
            return int(parity * 1.5), None

        safe_scored = []
        for e in safe_list:
            twos = 0
            for b in EDGE_BOXES[e]:
                s = (H & BOX_MASK_H[b]).bit_count() + (V & BOX_MASK_V[b]).bit_count()
                if s == 1:
                    twos += 1
            is_perim = len(EDGE_BOXES[e]) == 1
            safe_scored.append((twos, not is_perim, e))
        safe_scored.sort()
        moves = [e for _, _, e in safe_scored]
        if len(moves) > 6 and depth > 2:
            moves = moves[:6]
    else:
        # Only sacrifices exist: select moves giving away the smallest chain
        sac_scored = []
        for e in sacrifices_list:
            ch = _get_sacrifice_chain_length(e, H, V)
            sac_scored.append((ch, e))
        sac_scored.sort()
        min_ch = sac_scored[0][0]
        moves = [e for ch, e in sac_scored if ch == min_ch]

    best_val = -9999
    best_m = moves[0]
    orig_alpha = alpha

    for e in moves:
        if e < 20:
            nxt_H = H | (1 << e)
            nxt_V = V
        else:
            nxt_H = H
            nxt_V = V | (1 << (e - 20))

        c = 0
        for b in EDGE_BOXES[e]:
            s = (H & BOX_MASK_H[b]).bit_count() + (V & BOX_MASK_V[b]).bit_count()
            if s == 3:
                c += 1

        if c > 0:
            val, _ = _negamax(nxt_H, nxt_V, depth, alpha - c, beta - c,
                              start_time, max_time, tt, node_counter)
            val += c
        else:
            val, _ = _negamax(nxt_H, nxt_V, depth - 1, -beta, -alpha,
                              start_time, max_time, tt, node_counter)
            val = -val

        if val > best_val:
            best_val = val
            best_m = e
        alpha = max(alpha, val)
        if alpha >= beta:
            break

    flag = 0  # EXACT
    if best_val <= orig_alpha:
        flag = 2  # UPPERBOUND
    elif best_val >= beta:
        flag = 1  # LOWERBOUND

    if len(tt) < 150000:
        tt[state_key] = (depth, flag, best_val, best_m)

    return best_val, best_m


def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Returns the next move for Dots and Boxes on a 4x4 box grid.
    Output format: 'row,col,dir' where dir is 'H' or 'V'.
    """
    start_time = time.time()
    max_time = 0.70  # Conservative budget within the 1-second limit

    # Map arrays to 20-bit integer bitmasks
    H = 0
    h_rows = min(5, horizontal.shape[0])
    h_cols = min(4, horizontal.shape[1])
    for r in range(h_rows):
        for c in range(h_cols):
            if horizontal[r, c] != 0:
                H |= (1 << (r * 4 + c))

    V = 0
    v_rows = min(4, vertical.shape[0])
    v_cols = min(5, vertical.shape[1])
    for r in range(v_rows):
        for c in range(v_cols):
            if vertical[r, c] != 0:
                V |= (1 << (r * 5 + c))

    # Fast heuristic move as immediate baseline
    best_edge = _get_best_heuristic_move(H, V)

    # If the game is already in endgame or standard state, search deeper
    empty_count = 40 - H.bit_count() - V.bit_count()
    if best_edge is not None and empty_count > 1:
        tt = {}
        node_counter = [0]
        max_search_depth = 24 if empty_count <= 18 else 10

        for d in range(1, max_search_depth + 1):
            if time.time() - start_time > max_time:
                break
            try:
                score, m = _negamax(H, V, d, -1000, 1000, start_time, max_time, tt, node_counter)
                if m is not None:
                    best_edge = m
                if abs(score) >= 500:
                    break
            except TimeoutError:
                break

    if best_edge is not None:
        return EDGE_TO_STR[best_edge]

    # Universal fallback guaranteeing a legal move
    for r in range(horizontal.shape[0]):
        for c in range(horizontal.shape[1]):
            if horizontal[r, c] == 0:
                return f"{r},{c},H"

    for r in range(vertical.shape[0]):
        for c in range(vertical.shape[1]):
            if vertical[r, c] == 0:
                return f"{r},{c},V"

    return "0,0,H"
