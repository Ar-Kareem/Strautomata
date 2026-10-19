
import numpy as np
from functools import lru_cache

# Real 4x4-box board uses:
# - Horizontal edges: 5 rows x 4 cols = 20
# - Vertical edges:   4 rows x 5 cols = 20
# Total = 40 playable edges.

FULL_MASK = (1 << 40) - 1
ALL_MOVES = tuple(range(40))

ADJ_BOXES = [[] for _ in range(40)]
BOX_MASKS = []
MOVE_STR = []
BOUNDARY_BONUS = [0] * 40


def _h_idx(r, c):
    return r * 4 + c


def _v_idx(r, c):
    return 20 + r * 5 + c


# Precompute move strings and box adjacency.
for idx in range(40):
    if idx < 20:
        r, c = divmod(idx, 4)
        MOVE_STR.append(f"{r},{c},H")
    else:
        j = idx - 20
        r, c = divmod(j, 5)
        MOVE_STR.append(f"{r},{c},V")

for r in range(4):
    for c in range(4):
        edges = [
            _h_idx(r, c),       # top
            _h_idx(r + 1, c),   # bottom
            _v_idx(r, c),       # left
            _v_idx(r, c + 1),   # right
        ]
        mask = 0
        b = r * 4 + c
        for e in edges:
            mask |= (1 << e)
            ADJ_BOXES[e].append(b)
        BOX_MASKS.append(mask)

for idx in range(40):
    BOUNDARY_BONUS[idx] = 2 if len(ADJ_BOXES[idx]) == 1 else 0


def _arrays_to_mask(horizontal: np.ndarray, vertical: np.ndarray) -> int:
    mask = 0
    # Real horizontal edges: rows 0..4, cols 0..3
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] != 0:
                mask |= (1 << _h_idx(r, c))
    # Real vertical edges: rows 0..3, cols 0..4
    for r in range(4):
        for c in range(5):
            if vertical[r, c] != 0:
                mask |= (1 << _v_idx(r, c))
    return mask


def _fallback_legal_move(horizontal: np.ndarray, vertical: np.ndarray) -> str:
    # Prefer real board edges first.
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] == 0:
                return f"{r},{c},H"
    for r in range(4):
        for c in range(5):
            if vertical[r, c] == 0:
                return f"{r},{c},V"

    # Defensive fallback in case the environment uses all 5x5 cells.
    for r in range(horizontal.shape[0]):
        for c in range(horizontal.shape[1]):
            if horizontal[r, c] == 0:
                return f"{r},{c},H"
    for r in range(vertical.shape[0]):
        for c in range(vertical.shape[1]):
            if vertical[r, c] == 0:
                return f"{r},{c},V"

    # Should never happen in a valid nonterminal call.
    return "0,0,H"


def _move_features(mask: int, idx: int):
    """
    Returns:
      captures: number of boxes completed by playing idx
      threes:   adjacent boxes left with exactly 3 sides after the move
      twos:     adjacent boxes left with exactly 2 sides after the move
    """
    newmask = mask | (1 << idx)
    captures = 0
    threes = 0
    twos = 0
    for b in ADJ_BOXES[idx]:
        cnt = (newmask & BOX_MASKS[b]).bit_count()
        if cnt == 4:
            captures += 1
        elif cnt == 3:
            threes += 1
        elif cnt == 2:
            twos += 1
    return captures, threes, twos


def _local_move_score(mask: int, idx: int) -> int:
    captures, threes, twos = _move_features(mask, idx)
    safe = 1 if (captures == 0 and threes == 0) else 0
    return 100 * captures + 20 * safe - 8 * threes - twos + BOUNDARY_BONUS[idx]


@lru_cache(maxsize=None)
def _ordered_moves(mask: int):
    scored = []
    for idx in ALL_MOVES:
        if ((mask >> idx) & 1) == 0:
            scored.append((_local_move_score(mask, idx), idx))
    scored.sort(reverse=True)
    return tuple(idx for _, idx in scored)


@lru_cache(maxsize=None)
def _greedy_capture_run(mask: int) -> int:
    """
    Approximate how many boxes the side to move can keep capturing immediately
    if it greedily takes available captures. Used to estimate chain damage.
    """
    total = 0
    cur = mask
    while True:
        best_cap = 0
        best_idx = -1
        for idx in ALL_MOVES:
            if ((cur >> idx) & 1) == 0:
                cap, _, _ = _move_features(cur, idx)
                if cap > best_cap:
                    best_cap = cap
                    best_idx = idx
        if best_cap <= 0:
            break
        total += best_cap
        cur |= (1 << best_idx)
    return total


@lru_cache(maxsize=None)
def _solve_exact(mask: int, player: int) -> int:
    """
    Exact minimax from this occupancy state to the end.
    Returns future box differential from root perspective.
    player = 1 if it's our turn, -1 if opponent's turn.
    """
    if mask == FULL_MASK:
        return 0

    moves = _ordered_moves(mask)
    if player == 1:
        best = -999
        for idx in moves:
            cap, _, _ = _move_features(mask, idx)
            newmask = mask | (1 << idx)
            nxt = 1 if cap > 0 else -1
            val = cap + _solve_exact(newmask, nxt)
            if val > best:
                best = val
        return best
    else:
        best = 999
        for idx in moves:
            cap, _, _ = _move_features(mask, idx)
            newmask = mask | (1 << idx)
            nxt = -1 if cap > 0 else 1
            val = -cap + _solve_exact(newmask, nxt)
            if val < best:
                best = val
        return best


def _heuristic_eval(mask: int, player: int) -> float:
    """
    Heuristic estimate of future box differential from root perspective.
    """
    three_boxes = 0
    two_boxes = 0
    safe_moves = 0
    legal = []

    for bmask in BOX_MASKS:
        cnt = (mask & bmask).bit_count()
        if cnt == 3:
            three_boxes += 1
        elif cnt == 2:
            two_boxes += 1

    for idx in ALL_MOVES:
        if ((mask >> idx) & 1) == 0:
            legal.append(idx)
            cap, threes, _ = _move_features(mask, idx)
            if cap == 0 and threes == 0:
                safe_moves += 1

    # Side-to-move having many 3-sided boxes is strong.
    val = player * 1.6 * three_boxes
    # Many 2-sided boxes usually means chains are brewing.
    val -= 0.30 * two_boxes
    # Having safe moves is good.
    val += 0.08 * safe_moves

    # If no safe move and no immediate capture exists, someone must open.
    if legal and safe_moves == 0 and three_boxes == 0:
        best_damage = 99
        for idx in legal:
            dmg = _greedy_capture_run(mask | (1 << idx))
            if dmg < best_damage:
                best_damage = dmg
        val += -player * 1.1 * best_damage

    return val


def _search(mask: int, player: int, depth: int, alpha: float, beta: float) -> float:
    remaining = 40 - mask.bit_count()
    if remaining == 0:
        return 0.0

    # Exact solve in small endgames.
    if remaining <= 12:
        return float(_solve_exact(mask, player))

    if depth <= 0:
        return _heuristic_eval(mask, player)

    moves = list(_ordered_moves(mask))

    # Beam-style reduction in larger positions for speed.
    if remaining > 28 and len(moves) > 10:
        moves = moves[:10]
    elif remaining > 24 and len(moves) > 12:
        moves = moves[:12]
    elif remaining > 20 and len(moves) > 14:
        moves = moves[:14]

    if player == 1:
        best = -999.0
        for idx in moves:
            cap, _, _ = _move_features(mask, idx)
            newmask = mask | (1 << idx)
            nxt = 1 if cap > 0 else -1
            val = cap + _search(newmask, nxt, depth - 1, alpha, beta)
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        return best
    else:
        best = 999.0
        for idx in moves:
            cap, _, _ = _move_features(mask, idx)
            newmask = mask | (1 << idx)
            nxt = -1 if cap > 0 else 1
            val = -cap + _search(newmask, nxt, depth - 1, alpha, beta)
            if val < best:
                best = val
            if best < beta:
                beta = best
            if alpha >= beta:
                break
        return best


def _choose_exact_root(mask: int) -> int:
    best_move = _ordered_moves(mask)[0]
    best_val = -999
    for idx in _ordered_moves(mask):
        cap, _, _ = _move_features(mask, idx)
        newmask = mask | (1 << idx)
        nxt = 1 if cap > 0 else -1
        val = cap + _solve_exact(newmask, nxt)
        if val > best_val:
            best_val = val
            best_move = idx
    return best_move


def _choose_forced_opening(mask: int, legal_moves) -> int:
    """
    No safe moves and no immediate captures: open the move that seems to
    give away the smallest immediate chain.
    """
    best_move = legal_moves[0]
    best_score = -10**9
    for idx in legal_moves:
        cap, threes, twos = _move_features(mask, idx)
        # In this caller cap should be 0, but keep it robust.
        damage = _greedy_capture_run(mask | (1 << idx))
        score = -100 * damage - 10 * threes - twos + BOUNDARY_BONUS[idx] + 50 * cap
        if score > best_score:
            best_score = score
            best_move = idx
    return best_move


def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    try:
        mask = _arrays_to_mask(horizontal, vertical)
        legal = [idx for idx in ALL_MOVES if ((mask >> idx) & 1) == 0]

        if not legal:
            return _fallback_legal_move(horizontal, vertical)

        if len(legal) == 1:
            return MOVE_STR[legal[0]]

        captures_exist = False
        safe_exist = False
        for idx in legal:
            cap, threes, _ = _move_features(mask, idx)
            if cap > 0:
                captures_exist = True
            if cap == 0 and threes == 0:
                safe_exist = True

        remaining = len(legal)

        # Exact play in smaller/tactical positions.
        if remaining <= 14 or (captures_exist and remaining <= 16) or ((not safe_exist) and remaining <= 18):
            return MOVE_STR[_choose_exact_root(mask)]

        # Forced opening heuristic when there are no safe moves and no captures.
        if (not safe_exist) and (not captures_exist):
            return MOVE_STR[_choose_forced_opening(mask, legal)]

        # Otherwise do shallow tactical search.
        if captures_exist and remaining <= 24:
            depth = 4
        elif remaining > 26:
            depth = 2
        else:
            depth = 3

        moves = list(_ordered_moves(mask))
        if remaining > 28 and len(moves) > 12:
            moves = moves[:12]
        elif remaining > 24 and len(moves) > 14:
            moves = moves[:14]

        best_move = moves[0]
        best_val = -999.0
        alpha = -999.0
        beta = 999.0

        for idx in moves:
            cap, _, _ = _move_features(mask, idx)
            newmask = mask | (1 << idx)
            nxt = 1 if cap > 0 else -1
            val = cap + _search(newmask, nxt, depth - 1, alpha, beta)

            if val > best_val:
                best_val = val
                best_move = idx
            elif val == best_val:
                if _local_move_score(mask, idx) > _local_move_score(mask, best_move):
                    best_move = idx

            if val > alpha:
                alpha = val

        return MOVE_STR[best_move]

    except Exception:
        # Always return something legal.
        return _fallback_legal_move(horizontal, vertical)
