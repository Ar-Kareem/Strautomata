
import numpy as np
from functools import lru_cache

# Dots and Boxes: 4x4 boxes => 5x4 horizontal edges, 4x5 vertical edges.
# We represent occupancy as bitmasks:
#   hm: 20 bits for horizontal edges (r in 0..4, c in 0..3), idx=r*4+c
#   vm: 20 bits for vertical edges   (r in 0..3, c in 0..4), idx=r*5+c
# Captures as two 16-bit masks over boxes (r in 0..3, c in 0..3), idx=r*4+c:
#   cap1: boxes captured by us (player +1)
#   capm: boxes captured by opponent (player -1)


def _popcount(x: int) -> int:
    # Python 3.8+ has int.bit_count(), but keep compatibility.
    return x.bit_count() if hasattr(int, "bit_count") else bin(x).count("1")


# Precompute edge bits
H_BITS = [[1 << (r * 4 + c) for c in range(4)] for r in range(5)]
V_BITS = [[1 << (r * 5 + c) for c in range(5)] for r in range(4)]

# Precompute box edge masks (top,bottom,left,right) for each box (r,c)
BOX_EDGES = []
for br in range(4):
    for bc in range(4):
        top = H_BITS[br][bc]
        bot = H_BITS[br + 1][bc]
        left = V_BITS[br][bc]
        right = V_BITS[br][bc + 1]
        BOX_EDGES.append((top, bot, left, right))

# All possible moves in canonical order: (r, c, dir, bit)
ALL_MOVES = []
for r in range(5):
    for c in range(4):
        ALL_MOVES.append((r, c, "H", H_BITS[r][c]))
for r in range(4):
    for c in range(5):
        ALL_MOVES.append((r, c, "V", V_BITS[r][c]))


def _box_index(r: int, c: int) -> int:
    return r * 4 + c


def _is_box_complete(box_idx: int, hm: int, vm: int) -> bool:
    top, bot, left, right = BOX_EDGES[box_idx]
    return (hm & top) and (hm & bot) and (vm & left) and (vm & right)


def _box_filled_count(box_idx: int, hm: int, vm: int) -> int:
    top, bot, left, right = BOX_EDGES[box_idx]
    return int(bool(hm & top)) + int(bool(hm & bot)) + int(bool(vm & left)) + int(bool(vm & right))


def _count_three_sided_unclaimed(hm: int, vm: int, cap1: int, capm: int) -> int:
    claimed = cap1 | capm
    cnt = 0
    for i in range(16):
        if (claimed >> i) & 1:
            continue
        if _box_filled_count(i, hm, vm) == 3:
            cnt += 1
    return cnt


def _legal_moves(hm: int, vm: int):
    moves = []
    for r, c, d, bit in ALL_MOVES:
        if d == "H":
            if (hm & bit) == 0:
                moves.append((r, c, d, bit))
        else:
            if (vm & bit) == 0:
                moves.append((r, c, d, bit))
    return moves


def _apply_move(hm: int, vm: int, cap1: int, capm: int, player: int, move):
    r, c, d, bit = move
    # Occupy edge
    if d == "H":
        hm2 = hm | bit
        vm2 = vm
    else:
        hm2 = hm
        vm2 = vm | bit

    cap1_2, capm_2 = cap1, capm
    claimed = cap1_2 | capm_2
    captured = 0

    # Check up to two adjacent boxes for completion
    adj_boxes = []
    if d == "H":
        # Horizontal edge at (r,c) is bottom of box (r-1,c) and top of box (r,c)
        if r > 0:
            adj_boxes.append(_box_index(r - 1, c))
        if r < 4:
            adj_boxes.append(_box_index(r, c))
    else:
        # Vertical edge at (r,c) is right of box (r,c-1) and left of box (r,c)
        if c > 0:
            adj_boxes.append(_box_index(r, c - 1))
        if c < 4:
            adj_boxes.append(_box_index(r, c))

    for b in adj_boxes:
        if ((claimed >> b) & 1) == 1:
            continue
        if _is_box_complete(b, hm2, vm2):
            if player == 1:
                cap1_2 |= (1 << b)
            else:
                capm_2 |= (1 << b)
            claimed |= (1 << b)
            captured += 1

    next_player = player if captured > 0 else -player
    return hm2, vm2, cap1_2, capm_2, next_player, captured


def _state_eval(hm: int, vm: int, cap1: int, capm: int, player_to_move: int) -> int:
    # Strongly prioritize actual score.
    score_diff = _popcount(cap1) - _popcount(capm)

    # Terminal: all boxes captured or all edges filled
    edges_filled = _popcount(hm) + _popcount(vm)
    if (cap1 | capm) == 0xFFFF or edges_filled == 40:
        return score_diff * 10000

    # 3-sided unclaimed boxes are "immediate capture potential" for side to move.
    threes = _count_three_sided_unclaimed(hm, vm, cap1, capm)

    val = score_diff * 200
    # If it's our turn and there are 3-sided boxes, that's good (we can take them).
    # If it's opponent's turn and there are 3-sided boxes, that's bad (they can take them).
    val += (15 * threes) if (player_to_move == 1) else (-15 * threes)

    # Small preference for having more edges remaining early is unnecessary;
    # instead add a tiny bias against creating many 2-sided boxes? (kept minimal)
    return val


def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # Convert arrays to internal bitmasks (ignore signs; occupancy only)
    hm = 0
    for r in range(5):
        for c in range(4):
            if int(horizontal[r, c]) != 0:
                hm |= H_BITS[r][c]

    vm = 0
    for r in range(4):
        for c in range(5):
            if int(vertical[r, c]) != 0:
                vm |= V_BITS[r][c]

    cap1 = 0
    capm = 0
    for r in range(4):
        for c in range(4):
            v = int(capture[r, c])
            idx = _box_index(r, c)
            if v == 1:
                cap1 |= (1 << idx)
            elif v == -1:
                capm |= (1 << idx)

    remaining_edges = 40 - (_popcount(hm) + _popcount(vm))
    # Depth tuning for 1-second budget
    if remaining_edges <= 10:
        depth = 6
    elif remaining_edges <= 18:
        depth = 5
    elif remaining_edges <= 26:
        depth = 4
    else:
        depth = 3

    @lru_cache(maxsize=250000)
    def solve(hm_s: int, vm_s: int, cap1_s: int, capm_s: int, player_s: int, depth_s: int) -> int:
        if depth_s <= 0:
            return _state_eval(hm_s, vm_s, cap1_s, capm_s, player_s)

        edges_filled = _popcount(hm_s) + _popcount(vm_s)
        if edges_filled == 40 or (cap1_s | capm_s) == 0xFFFF:
            return _state_eval(hm_s, vm_s, cap1_s, capm_s, player_s)

        moves = _legal_moves(hm_s, vm_s)
        if not moves:
            return _state_eval(hm_s, vm_s, cap1_s, capm_s, player_s)

        # Order moves: captures first; among non-captures prefer those that don't hand 3-sides to opponent.
        scored = []
        for mv in moves:
            nh, nv, nc1, ncm, np, capcnt = _apply_move(hm_s, vm_s, cap1_s, capm_s, player_s, mv)
            threes_after = _count_three_sided_unclaimed(nh, nv, nc1, ncm)
            # If turn passes, threes_after is immediate risk; if we keep turn, it's less risky.
            risk = threes_after if (np != player_s) else 0
            # Higher is better for player_s; will flip later for minimizing player.
            mv_score = (capcnt * 1000) - (risk * 40)
            scored.append((mv_score, mv, nh, nv, nc1, ncm, np))

        scored.sort(key=lambda x: x[0], reverse=True)

        if player_s == 1:
            best = -10**18
            for _, mv, nh, nv, nc1, ncm, np in scored:
                val = solve(nh, nv, nc1, ncm, np, depth_s - 1)
                if val > best:
                    best = val
            return best
        else:
            # Opponent minimizes our evaluation
            best = 10**18
            # For opponent, reverse ordering helps a bit
            for _, mv, nh, nv, nc1, ncm, np in reversed(scored):
                val = solve(nh, nv, nc1, ncm, np, depth_s - 1)
                if val < best:
                    best = val
            return best

    # Root move choice for us (player=+1)
    legal = _legal_moves(hm, vm)
    if not legal:
        # Shouldn't happen unless game is over; return something deterministic.
        # Try to find any empty edge in the provided arrays as a last resort.
        for r in range(5):
            for c in range(4):
                if int(horizontal[r, c]) == 0:
                    return f"{r},{c},H"
        for r in range(4):
            for c in range(5):
                if int(vertical[r, c]) == 0:
                    return f"{r},{c},V"
        return "0,0,H"

    best_move = legal[0]
    best_val = -10**18

    # Root ordering similarly: captures first, then safer moves
    root_scored = []
    for mv in legal:
        nh, nv, nc1, ncm, np, capcnt = _apply_move(hm, vm, cap1, capm, 1, mv)
        threes_after = _count_three_sided_unclaimed(nh, nv, nc1, ncm)
        risk = threes_after if (np == -1) else 0
        mv_score = (capcnt * 1000) - (risk * 50)
        root_scored.append((mv_score, mv, nh, nv, nc1, ncm, np))
    root_scored.sort(key=lambda x: x[0], reverse=True)

    for _, mv, nh, nv, nc1, ncm, np in root_scored:
        val = solve(nh, nv, nc1, ncm, np, depth - 1)
        if val > best_val:
            best_val = val
            best_move = mv

    r, c, d, _ = best_move
    return f"{r},{c},{d}"
