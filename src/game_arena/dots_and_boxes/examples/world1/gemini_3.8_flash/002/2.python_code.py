
import time
import numpy as np

# ---------------------------------------------------------
# Precomputed Board Topology (4x4 boxes, 40 edges)
# ---------------------------------------------------------
# Horizontal edges: 5 rows x 4 cols = 20 edges (indices 0..19)
# Vertical edges:   4 rows x 5 cols = 20 edges (indices 20..39)
# Boxes:            4 rows x 4 cols = 16 boxes (indices 0..15)

BOX_EDGES = []
BOX_MASKS = []
for r in range(4):
    for c in range(4):
        top = r * 4 + c
        bottom = (r + 1) * 4 + c
        left = 20 + r * 5 + c
        right = 20 + r * 5 + (c + 1)
        BOX_EDGES.append((top, bottom, left, right))
        BOX_MASKS.append((1 << top) | (1 << bottom) | (1 << left) | (1 << right))

EDGE_BOXES = [[] for _ in range(40)]
for b, edges in enumerate(BOX_EDGES):
    for e in edges:
        EDGE_BOXES[e].append(b)
for e in range(40):
    EDGE_BOXES[e] = tuple(EDGE_BOXES[e])

ALL_EDGES_MASK = (1 << 40) - 1

if hasattr(int, "bit_count"):
    def popcount(x: int) -> int:
        return x.bit_count()
else:
    def popcount(x: int) -> int:
        return bin(x).count('1')

def edge_to_str(e: int) -> str:
    if e < 20:
        return f"{e // 4},{e % 4},H"
    else:
        v = e - 20
        return f"{v // 5},{v % 5},V"

def cascade_length(start_mask: int, move: int) -> int:
    m = start_mask | (1 << move)
    boxes_before = sum(1 for b in range(16) if (start_mask & BOX_MASKS[b]) == BOX_MASKS[b])
    while True:
        cap_edge = -1
        for b in range(16):
            if popcount(m & BOX_MASKS[b]) == 3:
                for e in BOX_EDGES[b]:
                    if not (m & (1 << e)):
                        cap_edge = e
                        break
                if cap_edge != -1:
                    break
        if cap_edge == -1:
            break
        m |= (1 << cap_edge)
    boxes_after = sum(1 for b in range(16) if (m & BOX_MASKS[b]) == BOX_MASKS[b])
    return boxes_after - boxes_before

def get_double_cross_moves(mask: int) -> list:
    deg3_boxes = [b for b in range(16) if popcount(mask & BOX_MASKS[b]) == 3]
    if len(deg3_boxes) != 1:
        return []
    b3 = deg3_boxes[0]
    b3_empty = [e for e in BOX_EDGES[b3] if not (mask & (1 << e))]
    if len(b3_empty) != 1:
        return []
    e_shared = b3_empty[0]
    adj = EDGE_BOXES[e_shared]
    if len(adj) != 2:
        return []
    b2 = adj[0] if adj[1] == b3 else adj[1]
    if popcount(mask & BOX_MASKS[b2]) != 2:
        return []
    
    b2_other_empty = [e for e in BOX_EDGES[b2] if not (mask & (1 << e)) and e != e_shared]
    dc_moves = []
    for e_dc in b2_other_empty:
        if all(popcount(mask & BOX_MASKS[b]) < 3 for b in EDGE_BOXES[e_dc]):
            dc_moves.append(e_dc)
    return dc_moves

def get_ordered_moves(mask: int) -> list:
    available = [e for e in range(40) if not (mask & (1 << e))]
    if not available:
        return []

    double_caps = []
    single_caps = []
    for e in available:
        caps = sum(1 for b in EDGE_BOXES[e] if popcount(mask & BOX_MASKS[b]) == 3)
        if caps == 2:
            double_caps.append(e)
        elif caps == 1:
            single_caps.append(e)

    if double_caps:
        return double_caps + single_caps

    if single_caps:
        uncompleted = 16 - sum(1 for b in range(16) if (mask & BOX_MASKS[b]) == BOX_MASKS[b])
        if uncompleted >= 4:
            dc_moves = get_double_cross_moves(mask)
            if dc_moves:
                return single_caps + dc_moves
        return single_caps

    safe_moves = []
    unsafe_moves = []
    for e in available:
        max_d = max(popcount(mask & BOX_MASKS[b]) for b in EDGE_BOXES[e])
        if max_d < 2:
            d_sum = sum(popcount(mask & BOX_MASKS[b]) for b in EDGE_BOXES[e])
            is_border = (len(EDGE_BOXES[e]) == 1)
            score = 3 if d_sum == 0 else (2 if is_border else (1 if d_sum == 1 else 0))
            safe_moves.append((score, e))
        else:
            unsafe_moves.append(e)

    if safe_moves:
        safe_moves.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in safe_moves]

    scored_unsafe = []
    for e in unsafe_moves:
        k = cascade_length(mask, e)
        scored_unsafe.append((k, e))
    scored_unsafe.sort(key=lambda x: x[0])
    return [e for _, e in scored_unsafe]

def heuristic_eval(mask: int) -> float:
    two_boxes_count = 0
    for b in range(16):
        if popcount(mask & BOX_MASKS[b]) == 2:
            two_boxes_count += 1
    
    safe_moves_count = 0
    for e in range(40):
        if not (mask & (1 << e)):
            if all(popcount(mask & BOX_MASKS[b]) < 2 for b in EDGE_BOXES[e]):
                safe_moves_count += 1
    
    if safe_moves_count > 0:
        return safe_moves_count * 0.1 - two_boxes_count * 0.05
    else:
        return -2.0 - two_boxes_count * 0.25

class SearchTimeout(Exception):
    pass

EXACT = 0
LOWERBOUND = 1
UPPERBOUND = 2

def alphabeta(mask: int, alpha: float, beta: float, depth: int,
              start_time: float, time_limit: float, tt: dict) -> tuple:
    if time.time() - start_time > time_limit:
        raise SearchTimeout()

    if mask == ALL_EDGES_MASK:
        return 0.0, -1

    tt_entry = tt.get(mask)
    if tt_entry is not None:
        tt_depth, tt_val, tt_move, tt_flag = tt_entry
        if tt_depth >= depth:
            if tt_flag == EXACT:
                return tt_val, tt_move
            elif tt_flag == LOWERBOUND and tt_val > alpha:
                alpha = tt_val
            elif tt_flag == UPPERBOUND and tt_val < beta:
                beta = tt_val
            if alpha >= beta:
                return tt_val, tt_move

    moves = get_ordered_moves(mask)
    if not moves:
        return 0.0, -1

    is_capture_phase = any(popcount(mask & BOX_MASKS[b]) == 3 for b in EDGE_BOXES[moves[0]])
    if depth <= 0 and not is_capture_phase:
        return heuristic_eval(mask), moves[0]

    best_val = -1000.0
    best_move = moves[0]
    orig_alpha = alpha

    if tt_entry is not None and tt_entry[2] in moves:
        tt_m = tt_entry[2]
        moves.remove(tt_m)
        moves.insert(0, tt_m)

    for m in moves:
        new_mask = mask | (1 << m)
        captured = 0
        for b in EDGE_BOXES[m]:
            if (new_mask & BOX_MASKS[b]) == BOX_MASKS[b]:
                captured += 1

        if captured > 0:
            val, _ = alphabeta(new_mask, alpha - captured, beta - captured, depth, start_time, time_limit, tt)
            val += captured
        else:
            val, _ = alphabeta(new_mask, -beta, -alpha, depth - 1, start_time, time_limit, tt)
            val = -val

        if val > best_val:
            best_val = val
            best_move = m

        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    if best_val <= orig_alpha:
        flag = UPPERBOUND
    elif best_val >= beta:
        flag = LOWERBOUND
    else:
        flag = EXACT

    if len(tt) < 200000:
        tt[mask] = (depth, best_val, best_move, flag)

    return best_val, best_move

# ---------------------------------------------------------
# Arena Policy Entry Point
# ---------------------------------------------------------
def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    mask = 0
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] != 0:
                mask |= (1 << (r * 4 + c))
    for r in range(4):
        for c in range(5):
            if vertical[r, c] != 0:
                mask |= (1 << (20 + r * 5 + c))

    moves = get_ordered_moves(mask)
    if not moves:
        for r in range(5):
            for c in range(5):
                if horizontal[r, c] == 0:
                    return f"{r},{c},H"
                if vertical[r, c] == 0:
                    return f"{r},{c},V"
        return "0,0,H"

    fallback_move = moves[0]
    start_time = time.time()
    time_limit = 0.82
    tt = {}

    best_move = fallback_move
    unplayed = 40 - popcount(mask)
    max_search_depth = min(unplayed, 18)

    for depth in range(1, max_search_depth + 1):
        try:
            _, move = alphabeta(mask, -1000.0, 1000.0, depth, start_time, time_limit, tt)
            if move != -1:
                best_move = move
            if depth >= unplayed:
                break
        except SearchTimeout:
            break

    return edge_to_str(best_move)
