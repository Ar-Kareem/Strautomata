
import time
import numpy as np

# -----------------------------
# Static board precomputation
# -----------------------------

TOTAL_EDGES = 40
ALL_EDGES = tuple(range(TOTAL_EDGES))

def _h_idx(r, c):
    return r * 4 + c  # 0..19

def _v_idx(r, c):
    return 20 + r * 5 + c  # 20..39

EDGE_BITS = tuple(1 << i for i in range(TOTAL_EDGES))

EDGE_TO_MOVE = [None] * TOTAL_EDGES
EDGE_BOXES = [None] * TOTAL_EDGES
BOX_MASKS = [0] * 16
BOX_SIDES = [None] * 16  # per box: ((edge, neighbor_box_or_None), ...)

# Horizontal edges
for r in range(5):
    for c in range(4):
        idx = _h_idx(r, c)
        EDGE_TO_MOVE[idx] = (r, c, 'H')
        boxes = []
        if r > 0:
            boxes.append((r - 1) * 4 + c)
        if r < 4:
            boxes.append(r * 4 + c)
        EDGE_BOXES[idx] = tuple(boxes)

# Vertical edges
for r in range(4):
    for c in range(5):
        idx = _v_idx(r, c)
        EDGE_TO_MOVE[idx] = (r, c, 'V')
        boxes = []
        if c > 0:
            boxes.append(r * 4 + (c - 1))
        if c < 4:
            boxes.append(r * 4 + c)
        EDGE_BOXES[idx] = tuple(boxes)

# Boxes
for r in range(4):
    for c in range(4):
        b = r * 4 + c
        top = _h_idx(r, c)
        bottom = _h_idx(r + 1, c)
        left = _v_idx(r, c)
        right = _v_idx(r, c + 1)
        BOX_MASKS[b] = EDGE_BITS[top] | EDGE_BITS[bottom] | EDGE_BITS[left] | EDGE_BITS[right]

        up_nb = (r - 1) * 4 + c if r > 0 else None
        down_nb = (r + 1) * 4 + c if r < 3 else None
        left_nb = r * 4 + (c - 1) if c > 0 else None
        right_nb = r * 4 + (c + 1) if c < 3 else None

        BOX_SIDES[b] = (
            (top, up_nb),
            (bottom, down_nb),
            (left, left_nb),
            (right, right_nb),
        )

# Global caches that are valid across calls.
_ANALYSIS_CACHE = {}
_COMPONENT_CACHE = {}
_EXACT_VALUE_CACHE = {}

# Search/config constants
TIME_BUDGET = 0.93
GENERAL_EXACT_REMAIN = 16
VOLATILE_EXACT_REMAIN = 22
HANDOUT_CANDIDATES = 4
MAX_DEPTH = 8

FLAG_EXACT = 0
FLAG_LOWER = 1
FLAG_UPPER = 2


# -----------------------------
# Utility helpers
# -----------------------------

def _move_to_str(edge_idx):
    r, c, d = EDGE_TO_MOVE[edge_idx]
    return f"{r},{c},{d}"

def _state_to_occ(horizontal, vertical):
    occ = 0
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] != 0:
                occ |= EDGE_BITS[_h_idx(r, c)]
    for r in range(4):
        for c in range(5):
            if vertical[r, c] != 0:
                occ |= EDGE_BITS[_v_idx(r, c)]
    return occ

def _emergency_move(horizontal, vertical):
    # First try only valid board edges.
    for e in ALL_EDGES:
        r, c, d = EDGE_TO_MOVE[e]
        if d == 'H':
            if horizontal[r, c] == 0:
                return f"{r},{c},H"
        else:
            if vertical[r, c] == 0:
                return f"{r},{c},V"

    # If the caller ever treats extra array cells as legal, fall back to any zero.
    for r in range(5):
        for c in range(5):
            if horizontal[r, c] == 0:
                return f"{r},{c},H"
    for r in range(5):
        for c in range(5):
            if vertical[r, c] == 0:
                return f"{r},{c},V"

    # Should never happen in a nonterminal call.
    return "0,0,H"


def _analyze_occ(occ):
    info = _ANALYSIS_CACHE.get(occ)
    if info is not None:
        return info

    box_counts = tuple((occ & mask).bit_count() for mask in BOX_MASKS)

    hist = [0] * 5
    for cnt in box_counts:
        hist[cnt] += 1

    legal = []
    captures = []
    safe = []
    cap_count = [0] * TOTAL_EDGES

    for e in ALL_EDGES:
        if occ & EDGE_BITS[e]:
            continue

        legal.append(e)

        k = 0
        safe_flag = True
        for b in EDGE_BOXES[e]:
            cnt = box_counts[b]
            if cnt == 3:
                k += 1
            if cnt == 2:
                safe_flag = False

        cap_count[e] = k
        if k > 0:
            captures.append(e)
        elif safe_flag:
            safe.append(e)

    info = {
        "legal": tuple(legal),
        "captures": tuple(captures),
        "safe": tuple(safe),
        "box_counts": box_counts,
        "hist": tuple(hist),
        "cap_count": tuple(cap_count),
    }
    _ANALYSIS_CACHE[occ] = info
    return info


def _components_occ(occ, box_counts=None):
    comp = _COMPONENT_CACHE.get(occ)
    if comp is not None:
        return comp

    if box_counts is None:
        box_counts = _analyze_occ(occ)["box_counts"]

    comp_id = [-1] * 16
    comp_lens = []

    for start in range(16):
        if box_counts[start] != 2 or comp_id[start] != -1:
            continue

        cid = len(comp_lens)
        stack = [start]
        comp_id[start] = cid
        size = 0

        while stack:
            b = stack.pop()
            size += 1
            for edge, nb in BOX_SIDES[b]:
                if nb is None:
                    continue
                if box_counts[nb] != 2:
                    continue
                if occ & EDGE_BITS[edge]:
                    continue
                if comp_id[nb] == -1:
                    comp_id[nb] = cid
                    stack.append(nb)

        comp_lens.append(size)

    comp = (tuple(comp_id), tuple(comp_lens))
    _COMPONENT_CACHE[occ] = comp
    return comp


def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # "capture" is not needed for move choice because current score is a constant
    # offset across all legal actions. Future value depends only on occupied edges.
    occ = _state_to_occ(horizontal, vertical)
    root_info = _analyze_occ(occ)

    if not root_info["legal"]:
        return _emergency_move(horizontal, vertical)

    deadline = time.perf_counter() + TIME_BUDGET
    node_counter = 0

    search_tt = {}
    exact_tt = {}

    class SearchTimeout(Exception):
        pass

    def check_time():
        nonlocal node_counter
        node_counter += 1
        if (node_counter & 1023) == 0 and time.perf_counter() >= deadline:
            raise SearchTimeout

    def probe_tt(table, key, alpha, beta):
        entry = table.get(key)
        if entry is None:
            return None, alpha, beta
        val, flag = entry
        if flag == FLAG_EXACT:
            return val, alpha, beta
        if flag == FLAG_LOWER:
            if val > alpha:
                alpha = val
        else:  # FLAG_UPPER
            if val < beta:
                beta = val
        if alpha >= beta:
            return val, alpha, beta
        return None, alpha, beta

    def safe_cost(box_counts, e):
        # Prefer touching untouched boxes; heavily dislike turning 1-sided boxes into 2-sided.
        cost = 0
        for b in EDGE_BOXES[e]:
            cnt = box_counts[b]
            cost += 1 if cnt == 0 else 3
        return cost

    def unsafe_key(occ0, info0, e):
        box_counts = info0["box_counts"]
        comp_id, comp_lens = _components_occ(occ0, box_counts)
        touched = set()
        for b in EDGE_BOXES[e]:
            if box_counts[b] == 2:
                cid = comp_id[b]
                if cid != -1:
                    touched.add(cid)
        loss = sum(comp_lens[cid] for cid in touched) if touched else 99
        return (loss, len(touched), len(EDGE_BOXES[e]), e)

    def order_capture_moves(occ0, info0, root=False):
        caps = list(info0["captures"])
        if not root:
            caps.sort(key=lambda e: (-info0["cap_count"][e], e))
            return caps

        scored = []
        for e in caps:
            child = _analyze_occ(occ0 | EDGE_BITS[e])
            scored.append((-info0["cap_count"][e], -len(child["captures"]), e))
        scored.sort()
        return [e for _, _, e in scored]

    def order_safe_moves(occ0, info0, root=False):
        safe_moves = list(info0["safe"])
        box_counts = info0["box_counts"]

        if not root:
            safe_moves.sort(key=lambda e: (safe_cost(box_counts, e), len(EDGE_BOXES[e]), e))
            return safe_moves

        scored = []
        for e in safe_moves:
            child = _analyze_occ(occ0 | EDGE_BITS[e])
            scored.append((len(child["safe"]), safe_cost(box_counts, e), len(EDGE_BOXES[e]), e))
        scored.sort()
        return [e for _, _, _, e in scored]

    def order_unsafe_moves(occ0, info0):
        moves = list(info0["legal"])
        moves.sort(key=lambda e: unsafe_key(occ0, info0, e))
        return moves

    def generate_moves(occ0, info0, exact=False, root=False):
        # Capture state
        if info0["captures"]:
            cap_moves = order_capture_moves(occ0, info0, root=root)

            # If safe moves exist elsewhere, taking boxes dominates delaying them.
            if info0["safe"]:
                return cap_moves

            # No safe moves: allow handouts / non-capturing transitions.
            other_moves = [e for e in info0["legal"] if info0["cap_count"][e] == 0]
            other_moves.sort(key=lambda e: unsafe_key(occ0, info0, e))

            if exact:
                return cap_moves + other_moves
            return cap_moves + other_moves[:HANDOUT_CANDIDATES]

        # Quiet safe state
        if info0["safe"]:
            return order_safe_moves(occ0, info0, root=root)

        # No captures, no safe moves: must open something.
        return order_unsafe_moves(occ0, info0)

    def heuristic(occ0, info0=None):
        if info0 is None:
            info0 = _analyze_occ(occ0)

        if not info0["legal"]:
            return 0.0

        # Search should usually avoid calling heuristic on tactical states,
        # but keep reasonable values as a fallback.
        if info0["captures"]:
            return float(max(info0["cap_count"][e] for e in info0["captures"]))

        if not info0["safe"]:
            best_loss = unsafe_key(occ0, info0, order_unsafe_moves(occ0, info0)[0])[0]
            return -float(best_loss)

        n_safe = len(info0["safe"])
        hist = info0["hist"]
        comp_id, comp_lens = _components_occ(occ0, info0["box_counts"])
        del comp_id  # unused, but kept for symmetry with cache return
        best_safe_cost = min(safe_cost(info0["box_counts"], e) for e in info0["safe"])

        score = 0.0
        score += 0.7 if (n_safe % 2 == 1) else -0.7
        score += 0.03 * n_safe
        score -= 0.20 * hist[2]
        score -= 0.08 * sum(max(0, L - 1) for L in comp_lens)
        score += 0.20 * (6 - best_safe_cost)
        return score

    def exact_value(occ0, alpha=-1e9, beta=1e9):
        check_time()

        cached_exact = _EXACT_VALUE_CACHE.get(occ0)
        if cached_exact is not None:
            return cached_exact

        info0 = _analyze_occ(occ0)
        if not info0["legal"]:
            _EXACT_VALUE_CACHE[occ0] = 0
            return 0

        alpha_in, beta_in = alpha, beta
        probed, alpha, beta = probe_tt(exact_tt, occ0, alpha, beta)
        if probed is not None:
            return probed

        moves = generate_moves(occ0, info0, exact=True, root=False)

        # Non-capturing moves consume a decision ply; exact search has no depth limit,
        # so only turn-switch logic matters here.
        best = -1e9
        for e in moves:
            k = info0["cap_count"][e]
            new_occ = occ0 | EDGE_BITS[e]
            if k > 0:
                val = k + exact_value(new_occ, alpha - k, beta - k)
            else:
                val = -exact_value(new_occ, -beta, -alpha)

            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

        flag = FLAG_EXACT
        if best <= alpha_in:
            flag = FLAG_UPPER
        elif best >= beta_in:
            flag = FLAG_LOWER

        exact_tt[occ0] = (best, flag)
        if flag == FLAG_EXACT:
            _EXACT_VALUE_CACHE[occ0] = best
        return best

    def search(occ0, depth, alpha=-1e9, beta=1e9):
        check_time()

        cached_exact = _EXACT_VALUE_CACHE.get(occ0)
        if cached_exact is not None:
            return cached_exact

        info0 = _analyze_occ(occ0)
        if not info0["legal"]:
            return 0.0

        remaining = len(info0["legal"])
        if remaining <= GENERAL_EXACT_REMAIN or ((not info0["safe"]) and remaining <= VOLATILE_EXACT_REMAIN):
            return exact_value(occ0, alpha, beta)

        # Only safe quiet states are allowed to stop at depth 0.
        if depth == 0 and (not info0["captures"]) and info0["safe"]:
            return heuristic(occ0, info0)

        key = (occ0, depth)
        alpha_in, beta_in = alpha, beta
        probed, alpha, beta = probe_tt(search_tt, key, alpha, beta)
        if probed is not None:
            return probed

        moves = generate_moves(occ0, info0, exact=False, root=False)

        # If we play a non-capturing move, the turn switches and we consume one decision ply.
        noncap_depth = depth - 1 if depth > 0 else 0

        best = -1e9
        for e in moves:
            k = info0["cap_count"][e]
            new_occ = occ0 | EDGE_BITS[e]

            if k > 0:
                val = k + search(new_occ, depth, alpha - k, beta - k)
            else:
                val = -search(new_occ, noncap_depth, -beta, -alpha)

            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

        flag = FLAG_EXACT
        if best <= alpha_in:
            flag = FLAG_UPPER
        elif best >= beta_in:
            flag = FLAG_LOWER
        search_tt[key] = (best, flag)
        return best

    def root_search(depth):
        info0 = _analyze_occ(occ)
        moves = generate_moves(occ, info0, exact=False, root=True)
        best_move = moves[0]
        best_val = -1e9
        alpha = -1e9
        beta = 1e9

        noncap_depth = depth - 1 if depth > 0 else 0

        for e in moves:
            k = info0["cap_count"][e]
            new_occ = occ | EDGE_BITS[e]

            if k > 0:
                val = k + search(new_occ, depth, alpha - k, beta - k)
            else:
                val = -search(new_occ, noncap_depth, -beta, -alpha)

            if val > best_val:
                best_val = val
                best_move = e
            if best_val > alpha:
                alpha = best_val

        return best_val, best_move

    def root_exact():
        info0 = _analyze_occ(occ)
        moves = generate_moves(occ, info0, exact=True, root=True)
        best_move = moves[0]
        best_val = -1e9
        alpha = -1e9
        beta = 1e9

        for e in moves:
            k = info0["cap_count"][e]
            new_occ = occ | EDGE_BITS[e]

            if k > 0:
                val = k + exact_value(new_occ, alpha - k, beta - k)
            else:
                val = -exact_value(new_occ, -beta, -alpha)

            if val > best_val:
                best_val = val
                best_move = e
            if best_val > alpha:
                alpha = best_val

        return best_val, best_move

    # Robust fallback move
    best_move = generate_moves(occ, root_info, exact=False, root=True)[0]

    # Try exact search in late/volatile positions first.
    try:
        rem = len(root_info["legal"])
        if rem <= GENERAL_EXACT_REMAIN or ((not root_info["safe"]) and rem <= VOLATILE_EXACT_REMAIN):
            _, best_move = root_exact()
    except SearchTimeout:
        pass

    # Iterative deepening search
    depth = 1
    while depth <= MAX_DEPTH and time.perf_counter() < deadline:
        try:
            _, move = root_search(depth)
            best_move = move
            depth += 1
        except SearchTimeout:
            break

    # Final legality check
    r, c, d = EDGE_TO_MOVE[best_move]
    if d == 'H':
        if horizontal[r, c] == 0:
            return f"{r},{c},H"
    else:
        if vertical[r, c] == 0:
            return f"{r},{c},V"

    return _emergency_move(horizontal, vertical)
