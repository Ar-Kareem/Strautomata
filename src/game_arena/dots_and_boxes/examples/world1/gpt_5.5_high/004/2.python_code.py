
import time
from functools import lru_cache
import numpy as np

# ---------- Board constants for a 4x4 boxes / 5x5 dots board ----------
# Real edges:
#   horizontal: rows 0..4, cols 0..3  -> 20 edges
#   vertical:   rows 0..3, cols 0..4  -> 20 edges

N = 4
NUM_BOXES = 16
NUM_EDGES = 40
FULL_EDGE_MASK = (1 << NUM_EDGES) - 1
FULL_BOX_MASK = (1 << NUM_BOXES) - 1

MOVE_INFO = []
MOVE_STR = []

def _h_idx(r, c):
    return r * 4 + c

def _v_idx(r, c):
    return 20 + r * 5 + c

for r in range(5):
    for c in range(4):
        MOVE_INFO.append((r, c, "H"))
        MOVE_STR.append(f"{r},{c},H")

for r in range(4):
    for c in range(5):
        MOVE_INFO.append((r, c, "V"))
        MOVE_STR.append(f"{r},{c},V")

BOX_MASK = []
EDGE_BOXES = [[] for _ in range(NUM_EDGES)]

for r in range(4):
    for c in range(4):
        b = r * 4 + c
        edges = [
            _h_idx(r, c),
            _h_idx(r + 1, c),
            _v_idx(r, c),
            _v_idx(r, c + 1),
        ]
        m = 0
        for e in edges:
            m |= 1 << e
            EDGE_BOXES[e].append(b)
        BOX_MASK.append(m)

EDGE_BOXES = [tuple(x) for x in EDGE_BOXES]


class _Timeout(Exception):
    pass


# ---------- Conversion and legality helpers ----------

def _arrays_to_masks(horizontal, vertical, capture):
    mask = 0
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] != 0:
                mask |= 1 << _h_idx(r, c)

    for r in range(4):
        for c in range(5):
            if vertical[r, c] != 0:
                mask |= 1 << _v_idx(r, c)

    claimed = 0
    for r in range(4):
        for c in range(4):
            if capture[r, c] != 0:
                claimed |= 1 << (r * 4 + c)

    return mask, claimed


def _idx_is_empty(idx, horizontal, vertical):
    r, c, d = MOVE_INFO[idx]
    if d == "H":
        return horizontal[r, c] == 0
    return vertical[r, c] == 0


def _fallback_any_legal(horizontal, vertical):
    # Prefer real Dots-and-Boxes edges.
    for idx in range(NUM_EDGES):
        try:
            if _idx_is_empty(idx, horizontal, vertical):
                return MOVE_STR[idx]
        except Exception:
            pass

    # If the arena treats the full 5x5 arrays as legal, this still returns
    # an empty array entry when no real edge is available.
    try:
        for r in range(5):
            for c in range(5):
                if horizontal[r, c] == 0:
                    return f"{r},{c},H"
        for r in range(5):
            for c in range(5):
                if vertical[r, c] == 0:
                    return f"{r},{c},V"
    except Exception:
        pass

    # Should only happen after the game is already over.
    return "0,0,H"


# ---------- Core game mechanics ----------

def _cap_count(mask, claimed, idx):
    bit = 1 << idx
    new_mask = mask | bit
    cnt = 0
    for b in EDGE_BOXES[idx]:
        bb = 1 << b
        if (claimed & bb) == 0 and (BOX_MASK[b] & new_mask) == BOX_MASK[b]:
            cnt += 1
    return cnt


def _apply_move(mask, claimed, idx):
    bit = 1 << idx
    new_mask = mask | bit
    gained_mask = 0
    gained = 0

    for b in EDGE_BOXES[idx]:
        bb = 1 << b
        if (claimed & bb) == 0 and (BOX_MASK[b] & new_mask) == BOX_MASK[b]:
            gained_mask |= bb
            gained += 1

    return new_mask, claimed | gained_mask, gained


def _is_safe_non_capture(mask, claimed, idx):
    # A non-capturing move is safe if it does not make an adjacent unclaimed
    # box have exactly 3 sides.
    for b in EDGE_BOXES[idx]:
        bb = 1 << b
        if claimed & bb:
            continue
        sides = (mask & BOX_MASK[b]).bit_count()
        if sides == 2:
            return False
    return True


def _classify(mask, claimed):
    caps = []
    safe = []
    unsafe = []

    free = FULL_EDGE_MASK ^ mask
    while free:
        lsb = free & -free
        idx = lsb.bit_length() - 1
        free -= lsb

        k = _cap_count(mask, claimed, idx)
        if k:
            caps.append((idx, k))
        elif _is_safe_non_capture(mask, claimed, idx):
            safe.append(idx)
        else:
            unsafe.append(idx)

    return caps, safe, unsafe


def _count_threat_boxes(mask, claimed):
    t = 0
    for b in range(NUM_BOXES):
        if claimed & (1 << b):
            continue
        if (mask & BOX_MASK[b]).bit_count() == 3:
            t += 1
    return t


def _count_two_sided(mask, claimed):
    t = 0
    for b in range(NUM_BOXES):
        if claimed & (1 << b):
            continue
        if (mask & BOX_MASK[b]).bit_count() == 2:
            t += 1
    return t


# ---------- Move ordering / tactical estimates ----------

def _forced_capture_count(mask, claimed):
    # Estimate the size of the chain/region available to the next player if
    # they simply take all immediately available captures.
    total = 0

    while True:
        best_idx = -1
        best_k = 0
        free = FULL_EDGE_MASK ^ mask

        while free:
            lsb = free & -free
            idx = lsb.bit_length() - 1
            free -= lsb
            k = _cap_count(mask, claimed, idx)
            if k > best_k:
                best_k = k
                best_idx = idx

        if best_k <= 0:
            return total

        mask, claimed, k = _apply_move(mask, claimed, best_idx)
        total += k


def _safe_score(mask, claimed, idx):
    # Higher is better. Prefer not to create 2-sided boxes; prefer low-contact
    # boundary moves early.
    risk = 0
    new_twos = 0
    adj = 0
    new_mask = mask | (1 << idx)

    for b in EDGE_BOXES[idx]:
        if claimed & (1 << b):
            continue
        adj += 1
        before = (mask & BOX_MASK[b]).bit_count()
        after = (new_mask & BOX_MASK[b]).bit_count()
        risk += before * before
        if after == 2:
            new_twos += 1

    # Mild deterministic center/boundary tie-break.
    r, c, d = MOVE_INFO[idx]
    center_penalty = abs(r - 2) + abs(c - 2)

    return -20 * new_twos - 4 * risk - adj - 0.05 * center_penalty


def _opener_score(mask, claimed, idx):
    # Higher is better for the player forced to open: open the smallest chain.
    nm, nc, _ = _apply_move(mask, claimed, idx)
    loss = _forced_capture_count(nm, nc)
    return -100 * loss + _safe_score(mask, claimed, idx)


def _general_order_score(mask, claimed, idx):
    k = _cap_count(mask, claimed, idx)
    if k:
        return 1000 + 100 * k
    if _is_safe_non_capture(mask, claimed, idx):
        return _safe_score(mask, claimed, idx)
    return -1000 + _opener_score(mask, claimed, idx)


def _ordered_moves(mask, claimed, depth, root=False):
    caps, safe, unsafe = _classify(mask, claimed)
    rem = NUM_EDGES - mask.bit_count()

    # At very small edge counts, consider every legal move.
    if rem <= 10:
        moves = [idx for idx, _ in caps] + safe + unsafe
        moves.sort(key=lambda i: _general_order_score(mask, claimed, i), reverse=True)
        return moves

    if caps:
        # Captures first, but include plausible hard-hearted handouts.
        caps.sort(key=lambda x: (-x[1], x[0]))
        cap_moves = [idx for idx, _ in caps]

        noncaps = safe + unsafe
        noncaps.sort(
            key=lambda i: _forced_capture_count((mask | (1 << i)), claimed)
            if _cap_count(mask, claimed, i) == 0 else 99
        )

        if root:
            limit = 12
        elif depth <= 2:
            limit = 3
        elif depth <= 5:
            limit = 5
        else:
            limit = 8

        return cap_moves + noncaps[:limit]

    if safe:
        safe.sort(key=lambda i: _safe_score(mask, claimed, i), reverse=True)
        if root:
            return safe
        if depth <= 2:
            return safe[:10]
        if depth <= 5:
            return safe[:14]
        return safe[:18]

    # No safe move: we are opening a chain/loop. Consider shortest openings.
    unsafe.sort(key=lambda i: _opener_score(mask, claimed, i), reverse=True)
    if root:
        return unsafe
    if rem <= 18:
        return unsafe
    if depth <= 3:
        return unsafe[:8]
    return unsafe[:12]


# ---------- Loony endgame component heuristic ----------

def _components(mask, claimed):
    visited = 0
    comps = []

    for start in range(NUM_BOXES):
        if claimed & (1 << start):
            continue
        if visited & (1 << start):
            continue

        stack = [start]
        visited |= 1 << start
        boxes = []
        boundary_missing = 0

        while stack:
            b = stack.pop()
            boxes.append(b)
            r, c = divmod(b, 4)

            # top
            e = _h_idx(r, c)
            if (mask & (1 << e)) == 0:
                if r == 0:
                    boundary_missing += 1
                else:
                    nb = b - 4
                    if claimed & (1 << nb):
                        boundary_missing += 1
                    elif (visited & (1 << nb)) == 0:
                        visited |= 1 << nb
                        stack.append(nb)

            # bottom
            e = _h_idx(r + 1, c)
            if (mask & (1 << e)) == 0:
                if r == 3:
                    boundary_missing += 1
                else:
                    nb = b + 4
                    if claimed & (1 << nb):
                        boundary_missing += 1
                    elif (visited & (1 << nb)) == 0:
                        visited |= 1 << nb
                        stack.append(nb)

            # left
            e = _v_idx(r, c)
            if (mask & (1 << e)) == 0:
                if c == 0:
                    boundary_missing += 1
                else:
                    nb = b - 1
                    if claimed & (1 << nb):
                        boundary_missing += 1
                    elif (visited & (1 << nb)) == 0:
                        visited |= 1 << nb
                        stack.append(nb)

            # right
            e = _v_idx(r, c + 1)
            if (mask & (1 << e)) == 0:
                if c == 3:
                    boundary_missing += 1
                else:
                    nb = b + 1
                    if claimed & (1 << nb):
                        boundary_missing += 1
                    elif (visited & (1 << nb)) == 0:
                        visited |= 1 << nb
                        stack.append(nb)

        length = len(boxes)
        is_loop = boundary_missing == 0
        handout_swing = 8 if is_loop else 4
        comps.append((length, handout_swing))

    comps.sort()
    return tuple(comps)


@lru_cache(None)
def _loony_value(comps):
    # Return margin for the player to move in a pure loony endgame.
    # Negative means the opener is losing boxes.
    if not comps:
        return 0

    best_for_opener = -999

    for i, (length, handout_swing) in enumerate(comps):
        rem = comps[:i] + comps[i + 1:]

        if not rem:
            value_if_opened = -length
        else:
            # Controller may take all and become opener, or make a handout.
            take_all = -length - _loony_value(rem)

            options = [take_all]
            if (handout_swing == 4 and length >= 3) or (handout_swing == 8 and length >= 4):
                handout = -length + handout_swing + _loony_value(rem)
                options.append(handout)

            # The opponent/controller chooses the worse result for opener.
            value_if_opened = min(options)

        if value_if_opened > best_for_opener:
            best_for_opener = value_if_opened

    return best_for_opener


# ---------- Evaluation and alpha-beta search ----------

def _heuristic(mask, claimed, side):
    # Value is from the original/root player's perspective.
    if claimed == FULL_BOX_MASK or mask == FULL_EDGE_MASK:
        return 0.0

    caps, safe, unsafe = _classify(mask, claimed)

    if not caps and not safe:
        comps = _components(mask, claimed)
        if comps:
            return float(side * _loony_value(comps))
        if unsafe:
            best_open = max(_opener_score(mask, claimed, i) for i in unsafe)
            return float(side * best_open / 100.0)

    threats = _count_threat_boxes(mask, claimed)
    twos = _count_two_sided(mask, claimed)

    val = 0.0
    val += side * 1.25 * threats

    if not caps:
        s = len(safe)
        if s:
            # Safe-move parity hint: making the opponent open is valuable.
            val += side * (0.20 if (s % 2 == 1) else -0.20)
            val += side * min(0.03 * s, 0.30)

    val -= side * 0.03 * twos
    return val


def _alphabeta(mask, claimed, side, depth, alpha, beta, deadline, tt, nodes):
    nodes[0] += 1
    if (nodes[0] & 1023) == 0 and time.perf_counter() > deadline:
        raise _Timeout()

    if claimed == FULL_BOX_MASK or mask == FULL_EDGE_MASK:
        return 0.0

    if depth < 0:
        depth = 0

    # Extend immediate-capture positions even at nominal leaf depth.
    if depth <= 0:
        caps, _, _ = _classify(mask, claimed)
        if not caps:
            return _heuristic(mask, claimed, side)

    key = (mask, claimed, side, depth)
    if key in tt:
        return tt[key]

    moves = _ordered_moves(mask, claimed, depth, root=False)
    if not moves:
        return 0.0

    cut = False

    if side == 1:
        value = -999.0
        for idx in moves:
            nm, nc, gained = _apply_move(mask, claimed, idx)
            nside = side if gained else -side
            ndepth = depth if gained else depth - 1

            score = gained + _alphabeta(nm, nc, nside, ndepth, alpha, beta, deadline, tt, nodes)

            if score > value:
                value = score
            if value > alpha:
                alpha = value
            if alpha >= beta:
                cut = True
                break
    else:
        value = 999.0
        for idx in moves:
            nm, nc, gained = _apply_move(mask, claimed, idx)
            nside = side if gained else -side
            ndepth = depth if gained else depth - 1

            score = -gained + _alphabeta(nm, nc, nside, ndepth, alpha, beta, deadline, tt, nodes)

            if score < value:
                value = score
            if value < beta:
                beta = value
            if alpha >= beta:
                cut = True
                break

    # Store only exact values, not cutoff bounds.
    if not cut:
        tt[key] = value

    return value


def _fallback_idx(mask, claimed):
    caps, safe, unsafe = _classify(mask, claimed)

    if caps:
        best_idx = caps[0][0]
        best_val = -9999.0
        for idx, k in caps:
            nm, nc, gained = _apply_move(mask, claimed, idx)
            val = 100 * gained + 2 * _count_threat_boxes(nm, nc) + _heuristic(nm, nc, 1)
            if val > best_val:
                best_val = val
                best_idx = idx
        return best_idx

    if safe:
        return max(safe, key=lambda i: _safe_score(mask, claimed, i))

    if unsafe:
        return max(unsafe, key=lambda i: _opener_score(mask, claimed, i))

    return 0


def _max_depth(mask, claimed):
    rem = NUM_EDGES - mask.bit_count()
    caps, safe, _ = _classify(mask, claimed)

    if rem <= 8:
        return 18
    if rem <= 12:
        return 16
    if rem <= 18:
        return 12
    if caps or not safe:
        return 10 if rem <= 24 else 8
    if rem <= 24:
        return 6
    if rem <= 32:
        return 4
    return 3


def _choose_move(mask, claimed):
    fallback = _fallback_idx(mask, claimed)

    if mask == FULL_EDGE_MASK:
        return fallback

    # Leave a little headroom under a 1 second arena limit.
    deadline = time.perf_counter() + 0.82
    max_depth = _max_depth(mask, claimed)
    tt = {}
    nodes = [0]

    root_moves = _ordered_moves(mask, claimed, max_depth, root=True)
    if fallback not in root_moves:
        root_moves.insert(0, fallback)

    complete_best = fallback

    for depth in range(1, max_depth + 1):
        if time.perf_counter() > deadline:
            break

        try:
            # Principal variation from previous iteration first.
            moves = root_moves
            if complete_best in moves:
                moves = [complete_best] + [m for m in moves if m != complete_best]

            best_idx = complete_best
            best_val = -999.0
            alpha = -999.0
            beta = 999.0

            for idx in moves:
                if time.perf_counter() > deadline:
                    raise _Timeout()

                nm, nc, gained = _apply_move(mask, claimed, idx)
                nside = 1 if gained else -1
                ndepth = depth if gained else depth - 1

                score = gained + _alphabeta(nm, nc, nside, ndepth, alpha, beta, deadline, tt, nodes)

                if score > best_val:
                    best_val = score
                    best_idx = idx
                if best_val > alpha:
                    alpha = best_val

            complete_best = best_idx

        except _Timeout:
            break

    return complete_best


# ---------- Required API ----------

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    try:
        mask, claimed = _arrays_to_masks(horizontal, vertical, capture)
        idx = _choose_move(mask, claimed)

        if 0 <= idx < NUM_EDGES and _idx_is_empty(idx, horizontal, vertical):
            return MOVE_STR[idx]

        return _fallback_any_legal(horizontal, vertical)

    except Exception:
        return _fallback_any_legal(horizontal, vertical)
