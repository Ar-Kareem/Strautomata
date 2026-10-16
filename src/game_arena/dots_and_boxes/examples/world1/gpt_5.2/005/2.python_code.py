
import numpy as np
import time
from typing import List, Tuple, Dict, Optional

# Dots and Boxes: 4x4 boxes => 5x5 dots
# Horizontal edges exist: rows 0..4, cols 0..3  (5*4 = 20)
# Vertical edges exist:   rows 0..3, cols 0..4  (4*5 = 20)
# Boxes exist: rows 0..3, cols 0..3 (16)

TOTAL_H = 20
TOTAL_V = 20
TOTAL_EDGES = TOTAL_H + TOTAL_V
TOTAL_BOXES = 16

INF = 10**9


class SearchTimeout(Exception):
    pass


# Precompute mappings for speed.
# Box index: b = r*4 + c
# h index: h = r*4 + c   where r in 0..4, c in 0..3
# v index: v = r*5 + c   where r in 0..3, c in 0..4

BOX_EDGES: List[Tuple[int, int, int, int]] = []  # (h_top, h_bottom, v_left, v_right)
H_EDGE_TO_BOXES: List[List[int]] = [[] for _ in range(TOTAL_H)]
V_EDGE_TO_BOXES: List[List[int]] = [[] for _ in range(TOTAL_V)]

for br in range(4):
    for bc in range(4):
        b = br * 4 + bc
        h_top = br * 4 + bc
        h_bottom = (br + 1) * 4 + bc
        v_left = br * 5 + bc
        v_right = br * 5 + (bc + 1)
        BOX_EDGES.append((h_top, h_bottom, v_left, v_right))

        H_EDGE_TO_BOXES[h_top].append(b)
        H_EDGE_TO_BOXES[h_bottom].append(b)
        V_EDGE_TO_BOXES[v_left].append(b)
        V_EDGE_TO_BOXES[v_right].append(b)


def _h_idx_to_rc(idx: int) -> Tuple[int, int]:
    return idx // 4, idx % 4


def _v_idx_to_rc(idx: int) -> Tuple[int, int]:
    return idx // 5, idx % 5


def _edge_occupied(hmask: int, vmask: int, is_h: bool, idx: int) -> bool:
    if is_h:
        return (hmask >> idx) & 1
    return (vmask >> idx) & 1


def _box_side_count(hmask: int, vmask: int, b: int) -> int:
    ht, hb, vl, vr = BOX_EDGES[b]
    return ((hmask >> ht) & 1) + ((hmask >> hb) & 1) + ((vmask >> vl) & 1) + ((vmask >> vr) & 1)


def _box_complete(hmask: int, vmask: int, b: int) -> bool:
    ht, hb, vl, vr = BOX_EDGES[b]
    m = ((hmask >> ht) & 1) & ((hmask >> hb) & 1) & ((vmask >> vl) & 1) & ((vmask >> vr) & 1)
    return bool(m)


def _legal_moves(hmask: int, vmask: int) -> List[Tuple[bool, int]]:
    moves: List[Tuple[bool, int]] = []
    # H
    for i in range(TOTAL_H):
        if ((hmask >> i) & 1) == 0:
            moves.append((True, i))
    # V
    for i in range(TOTAL_V):
        if ((vmask >> i) & 1) == 0:
            moves.append((False, i))
    return moves


def _move_capture_and_risk(hmask: int, vmask: int, cap_u: int, cap_o: int, move: Tuple[bool, int]) -> Tuple[int, int]:
    """
    Return (capture_count_if_played, risk_count_if_played)
    risk_count: number of adjacent unclaimed boxes that would become 3-sided (and unclaimed) after playing this edge.
    """
    is_h, idx = move
    adj = H_EDGE_TO_BOXES[idx] if is_h else V_EDGE_TO_BOXES[idx]
    cap_mask = cap_u | cap_o

    capture_cnt = 0
    risk_cnt = 0

    for b in adj:
        if (cap_mask >> b) & 1:
            continue  # already claimed
        sides = _box_side_count(hmask, vmask, b)
        # this edge is currently empty (only called for legal move), so:
        # if sides == 3 => this move captures that box
        if sides == 3:
            capture_cnt += 1
        # if sides == 2 => this move creates a 3-sided box (danger)
        elif sides == 2:
            risk_cnt += 1

    return capture_cnt, risk_cnt


def _apply_move(
    hmask: int, vmask: int, cap_u: int, cap_o: int, player: int, move: Tuple[bool, int]
) -> Tuple[int, int, int, int, int, bool]:
    """
    Apply move for 'player' (+1 or -1).
    Returns: (new_hmask, new_vmask, new_cap_u, new_cap_o, gained_boxes, extra_turn)
    """
    is_h, idx = move
    if is_h:
        new_h = hmask | (1 << idx)
        new_v = vmask
        adj = H_EDGE_TO_BOXES[idx]
    else:
        new_h = hmask
        new_v = vmask | (1 << idx)
        adj = V_EDGE_TO_BOXES[idx]

    cap_mask = cap_u | cap_o
    gained = 0
    new_cap_u = cap_u
    new_cap_o = cap_o

    for b in adj:
        if (cap_mask >> b) & 1:
            continue
        if _box_complete(new_h, new_v, b):
            gained += 1
            if player == 1:
                new_cap_u |= (1 << b)
            else:
                new_cap_o |= (1 << b)

    return new_h, new_v, new_cap_u, new_cap_o, gained, (gained > 0)


def _heuristic(hmask: int, vmask: int, cap_u: int, cap_o: int, player: int) -> float:
    """
    Heuristic value from the perspective of 'player' to move.
    """
    score_diff = cap_u.bit_count() - cap_o.bit_count()
    val = player * score_diff

    # Count immediately capturable boxes (3-sided, unclaimed).
    cap_mask = cap_u | cap_o
    capturable = 0
    two_sided = 0
    for b in range(TOTAL_BOXES):
        if (cap_mask >> b) & 1:
            continue
        sides = _box_side_count(hmask, vmask, b)
        if sides == 3:
            capturable += 1
        elif sides == 2:
            two_sided += 1

    # Capturable boxes are good for the player to move.
    val += 0.6 * capturable

    # Many 2-sided boxes mean there are many potential "third sides" to avoid; slight penalty.
    val -= 0.05 * two_sided

    # Mobility of safe moves: prefer having safe moves available.
    legal = _legal_moves(hmask, vmask)
    risky = 0
    for mv in legal:
        _, risk = _move_capture_and_risk(hmask, vmask, cap_u, cap_o, mv)
        if risk > 0:
            risky += 1
    safe = len(legal) - risky
    val += 0.02 * safe

    return val


def _qsearch(
    hmask: int, vmask: int, cap_u: int, cap_o: int, player: int,
    alpha: float, beta: float,
    tt: Dict[Tuple[int, int, int, int, int], Tuple[int, float]],
    deadline: float
) -> float:
    """
    Quiescence: only resolve capture moves (which keep the same player).
    """
    if time.perf_counter() > deadline:
        raise SearchTimeout

    key = (hmask, vmask, cap_u, cap_o, 2 if player == 1 else 1)
    # store with depth marker -1 for qsearch
    if key in tt and tt[key][0] == -1:
        return tt[key][1]

    legal = _legal_moves(hmask, vmask)
    cap_moves = []
    for mv in legal:
        cap_cnt, _ = _move_capture_and_risk(hmask, vmask, cap_u, cap_o, mv)
        if cap_cnt > 0:
            cap_moves.append((cap_cnt, mv))

    if not cap_moves:
        val = _heuristic(hmask, vmask, cap_u, cap_o, player)
        tt[key] = (-1, val)
        return val

    # Order: larger captures first
    cap_moves.sort(key=lambda x: -x[0])

    best = -INF
    for _, mv in cap_moves:
        nh, nv, ncu, nco, gained, extra = _apply_move(hmask, vmask, cap_u, cap_o, player, mv)
        # capture => extra should be True
        val = gained + _qsearch(nh, nv, ncu, nco, player, alpha, beta, tt, deadline)

        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    tt[key] = (-1, best)
    return best


def _negamax(
    hmask: int, vmask: int, cap_u: int, cap_o: int, player: int,
    depth: int, alpha: float, beta: float,
    tt: Dict[Tuple[int, int, int, int, int], Tuple[int, float]],
    deadline: float
) -> float:
    """
    Negamax for dots and boxes with extra turns:
      if capture: val = gained + negamax(same player)
      else:       val = -negamax(other player)
    Returned value is from perspective of 'player' to move.
    """
    if time.perf_counter() > deadline:
        raise SearchTimeout

    # Terminal: no moves
    if (hmask.bit_count() + vmask.bit_count()) == TOTAL_EDGES:
        return 0.0

    if depth <= 0:
        return _qsearch(hmask, vmask, cap_u, cap_o, player, alpha, beta, tt, deadline)

    key = (hmask, vmask, cap_u, cap_o, (2 if player == 1 else 1))
    if key in tt:
        stored_depth, stored_val = tt[key]
        if stored_depth >= depth:
            return stored_val

    legal = _legal_moves(hmask, vmask)

    # Move ordering: captures first, then low-risk.
    ordered: List[Tuple[int, int, Tuple[bool, int]]] = []
    for mv in legal:
        cap_cnt, risk = _move_capture_and_risk(hmask, vmask, cap_u, cap_o, mv)
        ordered.append((cap_cnt, -risk, mv))
    ordered.sort(key=lambda x: (x[0], x[1]), reverse=True)

    best = -INF
    a = alpha
    for cap_cnt, _, mv in ordered:
        nh, nv, ncu, nco, gained, extra = _apply_move(hmask, vmask, cap_u, cap_o, player, mv)
        if extra:
            val = gained + _negamax(nh, nv, ncu, nco, player, depth - 1, a, beta, tt, deadline)
        else:
            val = gained - _negamax(nh, nv, ncu, nco, -player, depth - 1, -beta, -a, tt, deadline)

        if val > best:
            best = val
        if best > a:
            a = best
        if a >= beta:
            break

    tt[key] = (depth, best)
    return best


def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # Build occupancy masks (ignore sign; only occupied vs empty matters for legality/completion).
    hmask = 0
    for r in range(5):
        for c in range(4):
            if int(horizontal[r, c]) != 0:
                hmask |= (1 << (r * 4 + c))

    vmask = 0
    for r in range(4):
        for c in range(5):
            if int(vertical[r, c]) != 0:
                vmask |= (1 << (r * 5 + c))

    cap_u = 0
    cap_o = 0
    for r in range(4):
        for c in range(4):
            v = int(capture[r, c])
            b = r * 4 + c
            if v == 1:
                cap_u |= (1 << b)
            elif v == -1:
                cap_o |= (1 << b)

    # Gather legal moves; must always return a legal move string.
    legal = _legal_moves(hmask, vmask)
    if not legal:
        # Game over (shouldn't happen), but return something syntactically valid.
        return "0,0,H"

    # Time management
    start = time.perf_counter()
    deadline = start + 0.90  # keep under 1s

    remaining = TOTAL_EDGES - (hmask.bit_count() + vmask.bit_count())

    # Choose max depth: solve exactly in late game, otherwise limited with iterative deepening.
    if remaining <= 18:
        max_depth = remaining  # exact to the end (captures can extend via extra turns)
    else:
        max_depth = 7

    # Root move ordering
    root_scored: List[Tuple[int, int, Tuple[bool, int]]] = []
    for mv in legal:
        cap_cnt, risk = _move_capture_and_risk(hmask, vmask, cap_u, cap_o, mv)
        root_scored.append((cap_cnt, -risk, mv))
    root_scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    root_moves = [mv for _, _, mv in root_scored]

    best_move = root_moves[0]
    best_val = -INF

    tt: Dict[Tuple[int, int, int, int, int], Tuple[int, float]] = {}

    # Iterative deepening
    for depth in range(1, max_depth + 1):
        if time.perf_counter() > deadline:
            break
        cur_best_move = best_move
        cur_best_val = -INF
        alpha = -INF
        beta = INF

        try:
            for mv in root_moves:
                if time.perf_counter() > deadline:
                    raise SearchTimeout

                nh, nv, ncu, nco, gained, extra = _apply_move(hmask, vmask, cap_u, cap_o, 1, mv)
                if extra:
                    val = gained + _negamax(nh, nv, ncu, nco, 1, depth - 1, alpha, beta, tt, deadline)
                else:
                    val = gained - _negamax(nh, nv, ncu, nco, -1, depth - 1, -beta, -alpha, tt, deadline)

                if val > cur_best_val:
                    cur_best_val = val
                    cur_best_move = mv
                if val > alpha:
                    alpha = val

            best_move = cur_best_move
            best_val = cur_best_val

        except SearchTimeout:
            break

    # Convert chosen move to "row,col,dir"
    is_h, idx = best_move
    if is_h:
        r, c = _h_idx_to_rc(idx)
        # Ensure legality against the provided arrays.
        if int(horizontal[r, c]) != 0:
            # fallback to any legal horizontal/vertical edge from arrays
            for rr in range(5):
                for cc in range(4):
                    if int(horizontal[rr, cc]) == 0:
                        return f"{rr},{cc},H"
            for rr in range(4):
                for cc in range(5):
                    if int(vertical[rr, cc]) == 0:
                        return f"{rr},{cc},V"
            return "0,0,H"
        return f"{r},{c},H"
    else:
        r, c = _v_idx_to_rc(idx)
        if int(vertical[r, c]) != 0:
            for rr in range(5):
                for cc in range(4):
                    if int(horizontal[rr, cc]) == 0:
                        return f"{rr},{cc},H"
            for rr in range(4):
                for cc in range(5):
                    if int(vertical[rr, cc]) == 0:
                        return f"{rr},{cc},V"
            return "0,0,H"
        return f"{r},{c},V"
