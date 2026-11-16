
import numpy as np
from functools import lru_cache

# Board geometry for a 4x4 box grid:
# Horizontal edges: rows 0..4, cols 0..3  -> 20 valid entries
# Vertical edges:   rows 0..3, cols 0..4  -> 20 valid entries
# Boxes:            rows 0..3, cols 0..3  -> 16 boxes

H_COUNT = 20
V_COUNT = 20
BOX_COUNT = 16
FULL_H = (1 << H_COUNT) - 1
FULL_V = (1 << V_COUNT) - 1

MOVE_KIND = []   # 0 = H, 1 = V
MOVE_ROW = []
MOVE_COL = []
MOVE_BIT = []
MOVE_ADJ = []    # tuple of adjacent box indices

BOX_H_MASK = [0] * BOX_COUNT
BOX_V_MASK = [0] * BOX_COUNT


def _h_idx(r, c):
    return r * 4 + c


def _v_idx(r, c):
    return r * 5 + c


def _b_idx(r, c):
    return r * 4 + c


# Precompute box masks
for br in range(4):
    for bc in range(4):
        b = _b_idx(br, bc)
        BOX_H_MASK[b] = (1 << _h_idx(br, bc)) | (1 << _h_idx(br + 1, bc))
        BOX_V_MASK[b] = (1 << _v_idx(br, bc)) | (1 << _v_idx(br, bc + 1))

# Precompute moves
# Horizontal moves
for r in range(5):
    for c in range(4):
        adj = []
        if r > 0:
            adj.append(_b_idx(r - 1, c))
        if r < 4:
            adj.append(_b_idx(r, c))
        MOVE_KIND.append(0)
        MOVE_ROW.append(r)
        MOVE_COL.append(c)
        MOVE_BIT.append(1 << _h_idx(r, c))
        MOVE_ADJ.append(tuple(adj))

# Vertical moves
for r in range(4):
    for c in range(5):
        adj = []
        if c > 0:
            adj.append(_b_idx(r, c - 1))
        if c < 4:
            adj.append(_b_idx(r, c))
        MOVE_KIND.append(1)
        MOVE_ROW.append(r)
        MOVE_COL.append(c)
        MOVE_BIT.append(1 << _v_idx(r, c))
        MOVE_ADJ.append(tuple(adj))

MOVE_COUNT = len(MOVE_KIND)  # 40


def _move_to_string(mi):
    d = 'H' if MOVE_KIND[mi] == 0 else 'V'
    return f"{MOVE_ROW[mi]},{MOVE_COL[mi]},{d}"


def _encode_masks(horizontal, vertical, capture):
    hmask = 0
    for r in range(5):
        for c in range(4):
            if int(horizontal[r, c]) != 0:
                hmask |= 1 << _h_idx(r, c)

    vmask = 0
    for r in range(4):
        for c in range(5):
            if int(vertical[r, c]) != 0:
                vmask |= 1 << _v_idx(r, c)

    cmask = 0
    for r in range(4):
        for c in range(4):
            if int(capture[r, c]) != 0:
                cmask |= 1 << _b_idx(r, c)

    return hmask, vmask, cmask


def _is_legal(hmask, vmask, mi):
    bit = MOVE_BIT[mi]
    if MOVE_KIND[mi] == 0:
        return (hmask & bit) == 0
    return (vmask & bit) == 0


def _box_sides(hmask, vmask, b):
    return (hmask & BOX_H_MASK[b]).bit_count() + (vmask & BOX_V_MASK[b]).bit_count()


def _move_gain(hmask, vmask, cmask, mi):
    gain = 0
    for b in MOVE_ADJ[mi]:
        if ((cmask >> b) & 1) == 0 and _box_sides(hmask, vmask, b) == 3:
            gain += 1
    return gain


def _move_creates_third(hmask, vmask, cmask, mi):
    # Count adjacent unclaimed boxes that currently have exactly 2 sides.
    # Playing here would make them 3-sided for the opponent.
    count = 0
    for b in MOVE_ADJ[mi]:
        if ((cmask >> b) & 1) == 0 and _box_sides(hmask, vmask, b) == 2:
            count += 1
    return count


def _apply_move(hmask, vmask, cmask, mi):
    bit = MOVE_BIT[mi]
    if MOVE_KIND[mi] == 0:
        hmask |= bit
    else:
        vmask |= bit

    gain = 0
    for b in MOVE_ADJ[mi]:
        if ((cmask >> b) & 1) == 0:
            if _box_sides(hmask, vmask, b) == 4:
                cmask |= 1 << b
                gain += 1

    return hmask, vmask, cmask, gain


def _classify_moves(hmask, vmask, cmask):
    legal = []
    captures = []
    safes = []
    risky = []

    for mi in range(MOVE_COUNT):
        if not _is_legal(hmask, vmask, mi):
            continue
        legal.append(mi)
        g = _move_gain(hmask, vmask, cmask, mi)
        if g > 0:
            captures.append(mi)
        else:
            t = _move_creates_third(hmask, vmask, cmask, mi)
            if t == 0:
                safes.append(mi)
            else:
                risky.append(mi)

    return legal, captures, safes, risky


def _count_safe_moves(hmask, vmask, cmask):
    cnt = 0
    for mi in range(MOVE_COUNT):
        if _is_legal(hmask, vmask, mi):
            if _move_gain(hmask, vmask, cmask, mi) == 0 and _move_creates_third(hmask, vmask, cmask, mi) == 0:
                cnt += 1
    return cnt


def _greedy_capture_total(hmask, vmask, cmask):
    # Repeatedly take any available capture, preferring larger immediate gain.
    total = 0
    for _ in range(BOX_COUNT):
        best_m = None
        best_g = 0
        for mi in range(MOVE_COUNT):
            if not _is_legal(hmask, vmask, mi):
                continue
            g = _move_gain(hmask, vmask, cmask, mi)
            if g > best_g:
                best_g = g
                best_m = mi
        if best_m is None or best_g == 0:
            break
        hmask, vmask, cmask, g = _apply_move(hmask, vmask, cmask, best_m)
        total += g
    return total, hmask, vmask, cmask


def _choose_safe_heuristic(hmask, vmask, cmask, safe_moves):
    best_m = safe_moves[0]
    best_score = None

    for mi in safe_moves:
        created_twos = 0
        sum_new_sides = 0
        for b in MOVE_ADJ[mi]:
            if ((cmask >> b) & 1) == 0:
                ns = _box_sides(hmask, vmask, b) + 1
                sum_new_sides += ns
                if ns == 2:
                    created_twos += 1

        boundary_bonus = 1 if len(MOVE_ADJ[mi]) == 1 else 0

        # Small tie-break lookahead
        nh, nv, nc, _ = _apply_move(hmask, vmask, cmask, mi)
        next_safe = _count_safe_moves(nh, nv, nc)

        score = (
            -created_twos,      # fewer new 2-sided boxes is better
            -sum_new_sides,     # keep adjacent boxes less developed
            boundary_bonus,     # boundary edges are often a little safer
            next_safe,          # keep the neutral phase alive
            -len(MOVE_ADJ[mi]), # fewer touched boxes
            -mi                 # deterministic
        )

        if best_score is None or score > best_score:
            best_score = score
            best_m = mi

    return best_m


def _choose_capture_heuristic(hmask, vmask, cmask, capture_moves):
    best_m = capture_moves[0]
    best_score = None

    for mi in capture_moves:
        nh, nv, nc, g = _apply_move(hmask, vmask, cmask, mi)
        extra, hh, hv, hc = _greedy_capture_total(nh, nv, nc)
        safe_after = _count_safe_moves(hh, hv, hc)

        score = (
            g + extra,   # strong preference for profitable capture sequences
            safe_after,  # better if neutral play still exists after harvesting
            g,           # immediate boxes
            -mi
        )

        if best_score is None or score > best_score:
            best_score = score
            best_m = mi

    return best_m


def _choose_forced_heuristic(hmask, vmask, cmask, legal_moves):
    # No safe moves: open the smallest chain we can.
    best_m = legal_moves[0]
    best_score = None

    for mi in legal_moves:
        nh, nv, nc, _ = _apply_move(hmask, vmask, cmask, mi)
        opp_gain, hh, hv, hc = _greedy_capture_total(nh, nv, nc)
        my_safe = _count_safe_moves(hh, hv, hc)
        boundary_bonus = 1 if len(MOVE_ADJ[mi]) == 1 else 0
        created = _move_creates_third(hmask, vmask, cmask, mi)

        score = (
            -opp_gain,       # minimize opponent's immediate harvest
            my_safe,         # better if we get back to a safer position
            -created,        # prefer opening fewer boxes at once
            boundary_bonus,
            -mi
        )

        if best_score is None or score > best_score:
            best_score = score
            best_m = mi

    return best_m


def _search_best_move(hmask, vmask, cmask):
    @lru_cache(maxsize=None)
    def solve(hm, vm, cm):
        best = None
        any_move = False

        for mi in range(MOVE_COUNT):
            if not _is_legal(hm, vm, mi):
                continue
            any_move = True
            nh, nv, nc, g = _apply_move(hm, vm, cm, mi)
            if g > 0:
                val = g + solve(nh, nv, nc)
            else:
                val = -solve(nh, nv, nc)

            if best is None or val > best:
                best = val

        return 0 if not any_move else best

    root_legal, _, _, _ = _classify_moves(hmask, vmask, cmask)
    if not root_legal:
        return None

    best_m = root_legal[0]
    best_val = None
    best_tie = None

    for mi in root_legal:
        nh, nv, nc, g = _apply_move(hmask, vmask, cmask, mi)
        if g > 0:
            val = g + solve(nh, nv, nc)
        else:
            val = -solve(nh, nv, nc)

        tie = (
            _move_gain(hmask, vmask, cmask, mi),
            -_move_creates_third(hmask, vmask, cmask, mi),
            1 if len(MOVE_ADJ[mi]) == 1 else 0,
            -mi
        )

        if best_val is None or val > best_val or (val == best_val and tie > best_tie):
            best_val = val
            best_tie = tie
            best_m = mi

    return best_m


def _first_legal_move(horizontal, vertical):
    # Prefer geometrically valid moves.
    for r in range(5):
        for c in range(4):
            if int(horizontal[r, c]) == 0:
                return f"{r},{c},H"
    for r in range(4):
        for c in range(5):
            if int(vertical[r, c]) == 0:
                return f"{r},{c},V"

    # Emergency fallback in case the environment uses extra valid entries.
    for r in range(5):
        for c in range(5):
            if int(horizontal[r, c]) == 0:
                return f"{r},{c},H"
    for r in range(5):
        for c in range(5):
            if int(vertical[r, c]) == 0:
                return f"{r},{c},V"

    # Should never happen in a normal call.
    return "0,0,H"


def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    try:
        hmask, vmask, cmask = _encode_masks(horizontal, vertical, capture)
        legal, captures, safes, risky = _classify_moves(hmask, vmask, cmask)

        if not legal:
            return _first_legal_move(horizontal, vertical)
        if len(legal) == 1:
            return _move_to_string(legal[0])

        remaining = (H_COUNT - hmask.bit_count()) + (V_COUNT - vmask.bit_count())

        # Use exact search in tactically critical or small positions.
        use_search = (
            remaining <= 16 or
            (len(captures) > 0 and remaining <= 20) or
            (len(safes) == 0 and remaining <= 24)
        )

        if use_search:
            best = _search_best_move(hmask, vmask, cmask)
            if best is not None and _is_legal(hmask, vmask, best):
                return _move_to_string(best)

        # Heuristic phases
        if captures:
            best = _choose_capture_heuristic(hmask, vmask, cmask, captures)
            return _move_to_string(best)

        if safes:
            best = _choose_safe_heuristic(hmask, vmask, cmask, safes)
            return _move_to_string(best)

        best = _choose_forced_heuristic(hmask, vmask, cmask, legal)
        return _move_to_string(best)

    except Exception:
        return _first_legal_move(horizontal, vertical)
