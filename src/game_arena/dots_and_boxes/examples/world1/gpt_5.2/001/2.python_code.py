
import numpy as np
from functools import lru_cache

# Board: 4x4 boxes => 5x5 dots
# We consider the standard playable edges:
#   Horizontal: r in [0..4], c in [0..3]  => 5*4 = 20
#   Vertical:   r in [0..3], c in [0..4]  => 4*5 = 20
# Total edges = 40, indexed 0..39.
#
# Edge index mapping:
#   H(r,c): idx = r*4 + c              (0..19)
#   V(r,c): idx = 20 + r*5 + c         (20..39)

ALL_EDGES = 40
ALL_EDGE_MASK = (1 << ALL_EDGES) - 1
NBOX = 16  # 4x4

# Precompute box edge masks and edge->boxes adjacency
BOX_EDGE_MASK = [0] * NBOX           # 16 masks (over 40 bits)
EDGE_TO_BOXES = [[] for _ in range(ALL_EDGES)]  # list of box indices adjacent to each edge


def _h_idx(r: int, c: int) -> int:
    return r * 4 + c


def _v_idx(r: int, c: int) -> int:
    return 20 + r * 5 + c


def _box_index(br: int, bc: int) -> int:
    return br * 4 + bc


def _init_precompute():
    for br in range(4):
        for bc in range(4):
            b = _box_index(br, bc)
            top = _h_idx(br, bc)
            bot = _h_idx(br + 1, bc)
            left = _v_idx(br, bc)
            right = _v_idx(br, bc + 1)
            mask = (1 << top) | (1 << bot) | (1 << left) | (1 << right)
            BOX_EDGE_MASK[b] = mask
            for e in (top, bot, left, right):
                EDGE_TO_BOXES[e].append(b)


_init_precompute()


def _edge_to_move(idx: int) -> str:
    if idx < 20:
        r = idx // 4
        c = idx % 4
        return f"{r},{c},H"
    else:
        t = idx - 20
        r = t // 5
        c = t % 5
        return f"{r},{c},V"


def _legal_edges_from_arrays(horizontal: np.ndarray, vertical: np.ndarray) -> list[int]:
    moves = []
    # Horizontal playable
    for r in range(5):
        for c in range(4):
            if int(horizontal[r, c]) == 0:
                moves.append(_h_idx(r, c))
    # Vertical playable
    for r in range(4):
        for c in range(5):
            if int(vertical[r, c]) == 0:
                moves.append(_v_idx(r, c))
    return moves


def _masks_from_state(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> tuple[int, int]:
    edge_mask = 0
    for r in range(5):
        for c in range(4):
            if int(horizontal[r, c]) != 0:
                edge_mask |= (1 << _h_idx(r, c))
    for r in range(4):
        for c in range(5):
            if int(vertical[r, c]) != 0:
                edge_mask |= (1 << _v_idx(r, c))

    claimed_mask = 0
    for r in range(4):
        for c in range(4):
            if int(capture[r, c]) != 0:
                claimed_mask |= (1 << _box_index(r, c))
    return edge_mask, claimed_mask


def _apply_move(edge_mask: int, claimed_mask: int, edge_idx: int) -> tuple[int, int, int]:
    """Return (new_edge_mask, new_claimed_mask, boxes_captured_now)."""
    new_edge_mask = edge_mask | (1 << edge_idx)
    new_claimed = claimed_mask
    cap = 0
    for b in EDGE_TO_BOXES[edge_idx]:
        bbit = 1 << b
        if (new_claimed & bbit) != 0:
            continue
        if (new_edge_mask & BOX_EDGE_MASK[b]).bit_count() == 4:
            new_claimed |= bbit
            cap += 1
    return new_edge_mask, new_claimed, cap


def _creates_third_side(edge_mask: int, claimed_mask: int, edge_idx: int) -> bool:
    """After playing edge_idx, does it create any unclaimed 3-sided box (for the opponent to finish)?"""
    new_edge_mask = edge_mask | (1 << edge_idx)
    for b in EDGE_TO_BOXES[edge_idx]:
        if (claimed_mask >> b) & 1:
            continue
        filled = (new_edge_mask & BOX_EDGE_MASK[b]).bit_count()
        if filled == 3:
            return True
    return False


def _count_new_thirds(edge_mask: int, claimed_mask: int, edge_idx: int) -> int:
    new_edge_mask = edge_mask | (1 << edge_idx)
    cnt = 0
    for b in EDGE_TO_BOXES[edge_idx]:
        if (claimed_mask >> b) & 1:
            continue
        filled = (new_edge_mask & BOX_EDGE_MASK[b]).bit_count()
        if filled == 3:
            cnt += 1
    return cnt


def _greedy_capture_run(edge_mask: int, claimed_mask: int, player: int) -> int:
    """
    Approximate best capture sequence for 'player' by greedily taking max-immediate-capture moves
    until no captures remain. Returns total boxes captured during this run.
    """
    total = 0
    em, cm = edge_mask, claimed_mask
    while True:
        remaining = (~em) & ALL_EDGE_MASK
        if remaining == 0:
            break

        best_edge = -1
        best_cap = 0
        # iterate all remaining edges
        rem = remaining
        while rem:
            lsb = rem & -rem
            e = (lsb.bit_length() - 1)
            rem -= lsb
            em2, cm2, cap = _apply_move(em, cm, e)
            if cap > best_cap:
                best_cap = cap
                best_edge = e
                if best_cap == 2:  # max possible from a single edge in this grid is 2
                    break

        if best_cap <= 0:
            break
        # take it and continue (extra turn)
        em, cm, cap = _apply_move(em, cm, best_edge)
        total += cap
    return total


def _fallback_any_legal(horizontal: np.ndarray, vertical: np.ndarray) -> str:
    # Prefer within standard playable edges
    legal = _legal_edges_from_arrays(horizontal, vertical)
    if legal:
        return _edge_to_move(min(legal))
    # If somehow none, search anywhere in 5x5 arrays for a 0 and return it.
    for r in range(5):
        for c in range(5):
            if int(horizontal[r, c]) == 0:
                return f"{r},{c},H"
    for r in range(5):
        for c in range(5):
            if int(vertical[r, c]) == 0:
                return f"{r},{c},V"
    # Terminal/no-legal; return something (engine should not call policy here).
    return "0,0,H"


def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    edge_mask, claimed_mask = _masks_from_state(horizontal, vertical, capture)
    legal = _legal_edges_from_arrays(horizontal, vertical)
    if not legal:
        return _fallback_any_legal(horizontal, vertical)

    remaining_edges = ALL_EDGES - edge_mask.bit_count()

    # --- Exact endgame search ---
    # Threshold tuned for strength vs. time.
    ENDGAME_THRESHOLD = 14

    if remaining_edges <= ENDGAME_THRESHOLD:
        # We only need claimed_mask (not owner) for future scoring; owner of already-claimed boxes is fixed.
        # Negamax returns best future box differential for the player to move.
        table = {}

        def ordered_moves(em: int, cm: int) -> list[int]:
            rem = (~em) & ALL_EDGE_MASK
            caps = []
            noncaps = []
            r = rem
            while r:
                lsb = r & -r
                e = (lsb.bit_length() - 1)
                r -= lsb
                _, _, cap = _apply_move(em, cm, e)
                if cap > 0:
                    # order captures first, bigger captures earlier
                    caps.append(( -cap, e))
                else:
                    # prefer "safe-ish" among non-captures
                    third = 1 if _creates_third_side(em, cm, e) else 0
                    noncaps.append((third, e))
            caps.sort()
            noncaps.sort()
            return [e for _, e in caps] + [e for _, e in noncaps]

        def negamax(em: int, cm: int, player: int, alpha: int, beta: int) -> int:
            key = (em, cm, player)
            if key in table:
                return table[key]

            rem = (~em) & ALL_EDGE_MASK
            if rem == 0:
                table[key] = 0
                return 0

            best = -10**9
            for e in ordered_moves(em, cm):
                em2, cm2, cap = _apply_move(em, cm, e)
                if cap > 0:
                    val = cap + negamax(em2, cm2, player, alpha, beta)
                else:
                    val = -negamax(em2, cm2, -player, -beta, -alpha)

                if val > best:
                    best = val
                if val > alpha:
                    alpha = val
                if alpha >= beta:
                    break

            table[key] = best
            return best

        best_move = legal[0]
        best_val = -10**9
        # Evaluate legal moves with full rules.
        for e in sorted(legal):
            em2, cm2, cap = _apply_move(edge_mask, claimed_mask, e)
            if cap > 0:
                val = cap + negamax(em2, cm2, 1, -10**9, 10**9)
            else:
                val = -negamax(em2, cm2, -1, -10**9, 10**9)
            if val > best_val:
                best_val = val
                best_move = e

        return _edge_to_move(best_move)

    # --- Midgame heuristic policy ---
    # 1) Take captures if available (prefer bigger captures, then fewer new 3-sides).
    capturing = []
    for e in legal:
        em2, cm2, cap = _apply_move(edge_mask, claimed_mask, e)
        if cap > 0:
            thirds = _count_new_thirds(edge_mask, claimed_mask, e)
            # score tuple: more capture better; fewer thirds better; deterministic tie-break by edge index
            capturing.append((cap, -thirds, -e, e))
    if capturing:
        capturing.sort(reverse=True)
        return _edge_to_move(capturing[0][3])

    # 2) Prefer safe moves (do not create any 3-sided box).
    safe = [e for e in legal if not _creates_third_side(edge_mask, claimed_mask, e)]
    if safe:
        # Choose the move that minimizes "risk": how many adjacent boxes it brings to 2 sides,
        # plus a small global "box tension" term.
        def risk_score(e: int) -> tuple:
            em2 = edge_mask | (1 << e)
            # local: count adjacent boxes that become 2-sided (closer to danger later)
            local_twos = 0
            for b in EDGE_TO_BOXES[e]:
                if (claimed_mask >> b) & 1:
                    continue
                filled = (em2 & BOX_EDGE_MASK[b]).bit_count()
                if filled == 2:
                    local_twos += 1
            # global: weighted sum over all unclaimed boxes (lightweight, still cheap on 16 boxes)
            global_score = 0
            for b in range(NBOX):
                if (claimed_mask >> b) & 1:
                    continue
                filled = (em2 & BOX_EDGE_MASK[b]).bit_count()
                # penalize approaching 3 (but safe moves ensure not 3 immediately)
                if filled == 2:
                    global_score += 3
                elif filled == 1:
                    global_score += 1
            return (local_twos, global_score, e)

        best = min(safe, key=risk_score)
        return _edge_to_move(best)

    # 3) Forced move (every move creates a 3-side): minimize opponent's immediate greedy capture run.
    best_e = legal[0]
    best_eval = 10**9
    for e in sorted(legal):
        em2, cm2, cap = _apply_move(edge_mask, claimed_mask, e)
        # No capture here by definition (we handled captures above), so opponent moves next.
        opp_gain = _greedy_capture_run(em2, cm2, player=-1)
        # Also prefer moves that create fewer distinct 3-sides (sometimes matters even if opp can’t take all)
        thirds = _count_new_thirds(edge_mask, claimed_mask, e)
        eval_tuple = (opp_gain, thirds, e)
        if eval_tuple < (best_eval, 10**9, 10**9):
            best_eval = eval_tuple[0]
            best_e = e

    return _edge_to_move(best_e)
