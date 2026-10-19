
import numpy as np
from functools import lru_cache

# Tactical search settings.
EXACT_THRESHOLD = 20  # exact solve when remaining standard edges <= 20

# --------------------------------------------------------------------
# Board geometry for a 4x4 box grid stored in padded 5x5 arrays.
# Valid edges:
#   Horizontal: rows 0..4, cols 0..3   => 20 edges
#   Vertical:   rows 0..3, cols 0..4   => 20 edges
# --------------------------------------------------------------------

ALL_MOVE_INDICES = tuple(range(40))
BIT = tuple(1 << i for i in range(40))

HIDX = [[-1] * 5 for _ in range(5)]
VIDX = [[-1] * 5 for _ in range(5)]
MOVE_TO_POS = []
MOVE_STR = []

idx = 0
for r in range(5):
    for c in range(4):
        HIDX[r][c] = idx
        MOVE_TO_POS.append((r, c, 'H'))
        MOVE_STR.append(f"{r},{c},H")
        idx += 1

for r in range(4):
    for c in range(5):
        VIDX[r][c] = idx
        MOVE_TO_POS.append((r, c, 'V'))
        MOVE_STR.append(f"{r},{c},V")
        idx += 1

FULL_MASK = (1 << 40) - 1

# Box indexing: b = 4 * row + col, rows/cols in 0..3
BOX_EDGES = []
BOX_MASK = []
for r in range(4):
    for c in range(4):
        edges = (
            HIDX[r][c],      # top
            HIDX[r + 1][c],  # bottom
            VIDX[r][c],      # left
            VIDX[r][c + 1],  # right
        )
        BOX_EDGES.append(edges)
        m = 0
        for e in edges:
            m |= BIT[e]
        BOX_MASK.append(m)
BOX_EDGES = tuple(BOX_EDGES)
BOX_MASK = tuple(BOX_MASK)

# Adjacent boxes for each move.
ADJ_BOXES = []
for i, (r, c, d) in enumerate(MOVE_TO_POS):
    boxes = []
    if d == 'H':
        if r > 0:
            boxes.append((r - 1) * 4 + c)
        if r < 4:
            boxes.append(r * 4 + c)
    else:  # 'V'
        if c > 0:
            boxes.append(r * 4 + (c - 1))
        if c < 4:
            boxes.append(r * 4 + c)
    ADJ_BOXES.append(tuple(boxes))
ADJ_BOXES = tuple(ADJ_BOXES)

# Neighbor boxes connected by a shared edge.
BOX_NEIGHBORS = []
for b in range(16):
    r, c = divmod(b, 4)
    neigh = []
    if r > 0:
        neigh.append(((r - 1) * 4 + c, HIDX[r][c]))
    if r < 3:
        neigh.append(((r + 1) * 4 + c, HIDX[r + 1][c]))
    if c > 0:
        neigh.append((r * 4 + (c - 1), VIDX[r][c]))
    if c < 3:
        neigh.append((r * 4 + (c + 1), VIDX[r][c + 1]))
    BOX_NEIGHBORS.append(tuple(neigh))
BOX_NEIGHBORS = tuple(BOX_NEIGHBORS)


# --------------------------------------------------------------------
# Basic helpers
# --------------------------------------------------------------------

def arrays_to_mask_and_legal(horizontal: np.ndarray, vertical: np.ndarray):
    mask = 0
    legal = []
    for i, (r, c, d) in enumerate(MOVE_TO_POS):
        val = horizontal[r, c] if d == 'H' else vertical[r, c]
        if val != 0:
            mask |= BIT[i]
        else:
            legal.append(i)
    return mask, legal


def build_box_counts(mask: int):
    # Number of drawn edges around each box.
    return [(mask & BOX_MASK[b]).bit_count() for b in range(16)]


def add_move_to_counts(counts, move_idx: int):
    new_counts = counts[:]
    for b in ADJ_BOXES[move_idx]:
        new_counts[b] += 1
    return new_counts


def gain_from_counts(counts, move_idx: int):
    g = 0
    for b in ADJ_BOXES[move_idx]:
        if counts[b] == 3:
            g += 1
    return g


def classify_moves(mask: int, counts=None):
    if counts is None:
        counts = build_box_counts(mask)

    captures = []  # list of (idx, gain)
    safes = []     # moves that do not create a 3-sided box
    others = []    # unsafe non-capturing moves

    for i in ALL_MOVE_INDICES:
        if mask & BIT[i]:
            continue

        g = 0
        unsafe = False
        for b in ADJ_BOXES[i]:
            cb = counts[b]
            if cb == 3:
                g += 1
            elif cb >= 2:
                unsafe = True

        if g > 0:
            captures.append((i, g))
        elif not unsafe:
            safes.append(i)
        else:
            others.append(i)

    return captures, safes, others


def count_safe_moves(mask: int, counts=None):
    if counts is None:
        counts = build_box_counts(mask)
    cnt = 0
    for i in ALL_MOVE_INDICES:
        if mask & BIT[i]:
            continue
        safe = True
        for b in ADJ_BOXES[i]:
            if counts[b] >= 2:
                safe = False
                break
        if safe:
            cnt += 1
    return cnt


def count_capture_moves(mask: int, counts=None):
    if counts is None:
        counts = build_box_counts(mask)
    cnt = 0
    for i in ALL_MOVE_INDICES:
        if mask & BIT[i]:
            continue
        for b in ADJ_BOXES[i]:
            if counts[b] == 3:
                cnt += 1
                break
    return cnt


def safe_order_key(counts, move_idx: int):
    new_two = sum(1 for b in ADJ_BOXES[move_idx] if counts[b] == 1)
    boundary = 0 if len(ADJ_BOXES[move_idx]) == 1 else 1
    return (1 if new_two == 2 else 0, new_two, boundary, move_idx)


def unsafe_order_key(counts, move_idx: int):
    opened = sum(1 for b in ADJ_BOXES[move_idx] if counts[b] == 2)
    boundary = 0 if len(ADJ_BOXES[move_idx]) == 1 else 1
    return (opened, boundary, move_idx)


# --------------------------------------------------------------------
# Chain / component heuristics
# --------------------------------------------------------------------

def degree2_component_lengths(mask: int, counts=None):
    if counts is None:
        counts = build_box_counts(mask)

    visited = [False] * 16
    lengths = []

    for b in range(16):
        if visited[b] or counts[b] != 2:
            continue

        stack = [b]
        visited[b] = True
        size = 0

        while stack:
            x = stack.pop()
            size += 1
            for nb, shared_edge in BOX_NEIGHBORS[x]:
                if counts[nb] == 2 and not (mask & BIT[shared_edge]) and not visited[nb]:
                    visited[nb] = True
                    stack.append(nb)

        lengths.append(size)

    return lengths


def component_penalty(mask: int, counts=None):
    lens = degree2_component_lengths(mask, counts)
    return sum(L * L for L in lens)


def is_pure_degree2(counts):
    for c in counts:
        if c not in (2, 4):
            return False
    return True


def open_smallest_chain_or_loop(mask: int, legal_moves, counts):
    visited = [False] * 16
    best_chain = None  # (length, edge)
    best_loop = None   # (length, edge)

    for b in range(16):
        if visited[b] or counts[b] != 2:
            continue

        stack = [b]
        visited[b] = True
        comp = []

        while stack:
            x = stack.pop()
            comp.append(x)
            for nb, shared_edge in BOX_NEIGHBORS[x]:
                if counts[nb] == 2 and not (mask & BIT[shared_edge]) and not visited[nb]:
                    visited[nb] = True
                    stack.append(nb)

        comp_set = set(comp)
        external_edges = []
        any_empty = None

        for x in comp:
            for e in BOX_EDGES[x]:
                if mask & BIT[e]:
                    continue
                if any_empty is None:
                    any_empty = e

                internal = False
                for ob in ADJ_BOXES[e]:
                    if ob != x and ob in comp_set:
                        internal = True
                        break
                if not internal:
                    external_edges.append(e)

        if external_edges:
            choice = (len(comp), min(external_edges))
            if best_chain is None or choice < best_chain:
                best_chain = choice
        else:
            choice = (len(comp), any_empty if any_empty is not None else legal_moves[0])
            if best_loop is None or choice < best_loop:
                best_loop = choice

    if best_chain is not None:
        return best_chain[1]
    if best_loop is not None:
        return best_loop[1]
    return min(legal_moves)


def greedy_capture_harvest(mask: int):
    # Approximate the number of boxes the side to move can immediately harvest
    # by greedily taking captures until none remain.
    cur = mask
    counts = build_box_counts(cur)
    total = 0

    while True:
        best_idx = -1
        best_gain = 0

        for i in ALL_MOVE_INDICES:
            if cur & BIT[i]:
                continue
            g = 0
            for b in ADJ_BOXES[i]:
                if counts[b] == 3:
                    g += 1
            if g > best_gain or (g == best_gain and g > 0 and (best_idx == -1 or i < best_idx)):
                best_gain = g
                best_idx = i

        if best_gain == 0:
            break

        total += best_gain
        cur |= BIT[best_idx]
        for b in ADJ_BOXES[best_idx]:
            counts[b] += 1

    return total, cur


def best_forced_open_loss(mask: int, legal_moves, counts=None):
    # If the current player is forced to open something, estimate the minimum
    # immediate harvest available to the opponent afterward.
    if not legal_moves:
        return 0, -1

    if counts is None:
        counts = build_box_counts(mask)

    if is_pure_degree2(counts):
        opener = open_smallest_chain_or_loop(mask, legal_moves, counts)
        loss, _ = greedy_capture_harvest(mask | BIT[opener])
        return loss, opener

    best_key = None
    best_idx = legal_moves[0]
    best_loss = 0

    for i in legal_moves:
        loss, after = greedy_capture_harvest(mask | BIT[i])
        after_counts = build_box_counts(after)
        my_caps = count_capture_moves(after, after_counts)
        my_safe = count_safe_moves(after, after_counts)

        key = (
            loss,
            0 if my_caps > 0 else 1,
            -my_caps,
            0 if my_safe > 0 else 1,
            -my_safe,
            i,
        )
        if best_key is None or key < best_key:
            best_key = key
            best_idx = i
            best_loss = loss

    return best_loss, best_idx


# --------------------------------------------------------------------
# Midgame move selection
# --------------------------------------------------------------------

def choose_safe_heuristic(mask: int, safe_moves, counts):
    best_key = None
    best_idx = safe_moves[0]

    for i in safe_moves:
        nm = mask | BIT[i]
        next_counts = add_move_to_counts(counts, i)
        opp_safe = count_safe_moves(nm, next_counts)

        new_two = sum(1 for b in ADJ_BOXES[i] if counts[b] == 1)
        new_one = sum(1 for b in ADJ_BOXES[i] if counts[b] == 0)
        boundary = 0 if len(ADJ_BOXES[i]) == 1 else 1
        comp_pen = component_penalty(nm, next_counts)

        if opp_safe == 0:
            legal_after = [j for j in ALL_MOVE_INDICES if not (nm & BIT[j])]
            forced_loss, _ = best_forced_open_loss(nm, legal_after, next_counts)
            key = (
                0,                 # best class: forces opponent to open
                -forced_loss,      # larger opponent loss is better
                1 if new_two == 2 else 0,
                new_two,
                comp_pen,
                boundary,
                i,
            )
        else:
            key = (
                1,
                1 if new_two == 2 else 0,
                new_two,
                comp_pen,
                opp_safe,
                boundary,
                new_one,
                i,
            )

        if best_key is None or key < best_key:
            best_key = key
            best_idx = i

    return best_idx


def choose_capture_heuristic(mask: int, capture_moves, counts):
    best_score = None
    best_idx = capture_moves[0]

    for i in capture_moves:
        g = gain_from_counts(counts, i)
        nm = mask | BIT[i]
        next_counts = add_move_to_counts(counts, i)

        if nm == FULL_MASK:
            end_state = 1
            next_caps = 0
            next_safe = 0
            forced_loss = 0
            comp_pen = 0
        else:
            end_state = 0
            next_caps = count_capture_moves(nm, next_counts)
            next_safe = count_safe_moves(nm, next_counts)
            comp_pen = component_penalty(nm, next_counts)

            if next_caps == 0 and next_safe == 0:
                legal_after = [j for j in ALL_MOVE_INDICES if not (nm & BIT[j])]
                forced_loss, _ = best_forced_open_loss(nm, legal_after, next_counts)
            else:
                forced_loss = 0

        control = 1 if (end_state or next_caps > 0 or next_safe > 0) else 0

        score = (
            g,
            end_state,
            control,
            next_caps,
            next_safe,
            -forced_loss,
            -comp_pen,
            -i,  # smaller index as final tie-break
        )

        if best_score is None or score > best_score:
            best_score = score
            best_idx = i

    return best_idx


# --------------------------------------------------------------------
# Exact search for tactical late game
# --------------------------------------------------------------------

def choose_best_exact(mask: int):
    @lru_cache(maxsize=None)
    def solve(m: int) -> int:
        if m == FULL_MASK:
            return 0

        counts = build_box_counts(m)
        captures, safes, others = classify_moves(m, counts)

        # Dominance pruning:
        # - If captures exist and safe moves also exist, capture first.
        # - If no captures but safe moves exist, play safe first.
        # - If captures exist and no safe moves exist, handout choices matter,
        #   so both captures and unsafe moves are considered.
        if captures:
            cap_order = [i for i, _ in sorted(captures, key=lambda p: (-p[1], p[0]))]
            if safes:
                cand = cap_order
            else:
                other_order = sorted(others, key=lambda x: unsafe_order_key(counts, x))
                cand = cap_order + other_order
        elif safes:
            cand = sorted(safes, key=lambda x: safe_order_key(counts, x))
        else:
            cand = sorted(others, key=lambda x: unsafe_order_key(counts, x))

        best = -99
        for i in cand:
            g = gain_from_counts(counts, i)
            nm = m | BIT[i]
            if g > 0:
                val = g + solve(nm)
            else:
                val = -solve(nm)
            if val > best:
                best = val

        return 0 if best == -99 else best

    counts = build_box_counts(mask)
    captures, safes, others = classify_moves(mask, counts)

    if captures:
        cap_order = [i for i, _ in sorted(captures, key=lambda p: (-p[1], p[0]))]
        if safes:
            cand = cap_order
        else:
            other_order = sorted(others, key=lambda x: unsafe_order_key(counts, x))
            cand = cap_order + other_order
    elif safes:
        cand = sorted(safes, key=lambda x: safe_order_key(counts, x))
    else:
        cand = sorted(others, key=lambda x: unsafe_order_key(counts, x))

    best_idx = cand[0]
    best_val = -99

    for i in cand:
        g = gain_from_counts(counts, i)
        nm = mask | BIT[i]
        if g > 0:
            val = g + solve(nm)
        else:
            val = -solve(nm)
        if val > best_val or (val == best_val and i < best_idx):
            best_val = val
            best_idx = i

    return best_idx


# --------------------------------------------------------------------
# Main policy
# --------------------------------------------------------------------

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    mask, legal_moves = arrays_to_mask_and_legal(horizontal, vertical)

    # Standard board exhausted? Fallback to any zero entry anywhere to stay legal.
    if not legal_moves:
        for r in range(horizontal.shape[0]):
            for c in range(horizontal.shape[1]):
                if horizontal[r, c] == 0:
                    return f"{r},{c},H"
        for r in range(vertical.shape[0]):
            for c in range(vertical.shape[1]):
                if vertical[r, c] == 0:
                    return f"{r},{c},V"
        return "0,0,H"

    counts = build_box_counts(mask)
    captures, safes, others = classify_moves(mask, counts)
    capture_moves = [i for i, _ in captures]
    remaining = len(legal_moves)

    # Exact tactical search.
    if remaining <= EXACT_THRESHOLD or (remaining == EXACT_THRESHOLD + 1 and (capture_moves or not safes)):
        return MOVE_STR[choose_best_exact(mask)]

    # Heuristic midgame.
    if capture_moves:
        return MOVE_STR[choose_capture_heuristic(mask, capture_moves, counts)]

    if safes:
        return MOVE_STR[choose_safe_heuristic(mask, safes, counts)]

    # Forced opening.
    _, opener = best_forced_open_loss(mask, others, counts)
    if opener != -1:
        return MOVE_STR[opener]

    # Final safety fallback.
    i = legal_moves[0]
    return MOVE_STR[i]
