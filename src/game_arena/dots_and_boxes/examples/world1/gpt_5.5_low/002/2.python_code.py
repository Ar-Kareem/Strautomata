
import numpy as np
from functools import lru_cache


# Dots and Boxes policy for a 4x4 box board.
# Valid horizontal edges: horizontal[0..4, 0..3]
# Valid vertical edges:   vertical[0..3, 0..4]


def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    H_ROWS, H_COLS = 5, 4
    V_ROWS, V_COLS = 4, 5
    N_H = 20
    N_E = 40

    def h_idx(r, c):
        return r * 4 + c

    def v_idx(r, c):
        return 20 + r * 5 + c

    def move_to_idx(move):
        r, c, d = move
        return h_idx(r, c) if d == "H" else v_idx(r, c)

    def idx_to_move(idx):
        if idx < 20:
            return (idx // 4, idx % 4, "H")
        idx -= 20
        return (idx // 5, idx % 5, "V")

    def move_str(move):
        r, c, d = move
        return f"{r},{c},{d}"

    def legal_moves_from_arrays():
        moves = []
        for r in range(5):
            for c in range(4):
                if horizontal[r, c] == 0:
                    moves.append((r, c, "H"))
        for r in range(4):
            for c in range(5):
                if vertical[r, c] == 0:
                    moves.append((r, c, "V"))
        return moves

    legal_moves = legal_moves_from_arrays()
    if not legal_moves:
        # Should not be called on a terminal state, but keep a syntactically valid fallback.
        return "0,0,H"

    # Build bitmasks for fast search.
    occ_mask = 0
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] != 0:
                occ_mask |= 1 << h_idx(r, c)
    for r in range(4):
        for c in range(5):
            if vertical[r, c] != 0:
                occ_mask |= 1 << v_idx(r, c)

    cap_mask = 0
    for r in range(4):
        for c in range(4):
            if capture[r, c] != 0:
                cap_mask |= 1 << (r * 4 + c)

    def affected_boxes(move):
        r, c, d = move
        boxes = []
        if d == "H":
            if r > 0:
                boxes.append((r - 1, c))
            if r < 4:
                boxes.append((r, c))
        else:
            if c > 0:
                boxes.append((r, c - 1))
            if c < 4:
                boxes.append((r, c))
        return boxes

    def box_sides_mask(mask, br, bc):
        cnt = 0
        if mask & (1 << h_idx(br, bc)):
            cnt += 1
        if mask & (1 << h_idx(br + 1, bc)):
            cnt += 1
        if mask & (1 << v_idx(br, bc)):
            cnt += 1
        if mask & (1 << v_idx(br, bc + 1)):
            cnt += 1
        return cnt

    def capture_count_after(mask, cmask, move):
        idx = move_to_idx(move)
        new_mask = mask | (1 << idx)
        made = 0
        for br, bc in affected_boxes(move):
            b = br * 4 + bc
            if not (cmask & (1 << b)) and box_sides_mask(new_mask, br, bc) == 4:
                made += 1
        return made

    def apply_move(mask, cmask, move):
        idx = move_to_idx(move)
        new_mask = mask | (1 << idx)
        gained = 0
        new_cmask = cmask
        for br, bc in affected_boxes(move):
            b = br * 4 + bc
            if not (new_cmask & (1 << b)) and box_sides_mask(new_mask, br, bc) == 4:
                new_cmask |= 1 << b
                gained += 1
        return new_mask, new_cmask, gained

    def creates_third_side(mask, cmask, move):
        idx = move_to_idx(move)
        new_mask = mask | (1 << idx)
        for br, bc in affected_boxes(move):
            b = br * 4 + bc
            if not (cmask & (1 << b)) and box_sides_mask(new_mask, br, bc) == 3:
                return True
        return False

    def all_empty_indices(mask):
        return [i for i in range(N_E) if not (mask & (1 << i))]

    remaining = len(legal_moves)

    # Exact negamax search for small endgames.
    # Value is future box differential for the player to move.
    if remaining <= 14:
        @lru_cache(None)
        def search(mask, cmask):
            if mask == (1 << N_E) - 1:
                return 0

            best = -1000

            # Captures first improves pruning-like behavior even without alpha-beta.
            empties = all_empty_indices(mask)
            scored = []
            quiet = []
            for idx in empties:
                mv = idx_to_move(idx)
                g = capture_count_after(mask, cmask, mv)
                if g:
                    scored.append((idx, g))
                else:
                    quiet.append((idx, g))

            ordered = scored + quiet

            for idx, _ in ordered:
                mv = idx_to_move(idx)
                nmask, ncmask, gained = apply_move(mask, cmask, mv)
                if gained:
                    val = gained + search(nmask, ncmask)
                else:
                    val = -search(nmask, ncmask)
                if val > best:
                    best = val
            return best

        best_move = None
        best_val = -1000
        for mv in legal_moves:
            nmask, ncmask, gained = apply_move(occ_mask, cap_mask, mv)
            if gained:
                val = gained + search(nmask, ncmask)
            else:
                val = -search(nmask, ncmask)
            if val > best_val:
                best_val = val
                best_move = mv

        if best_move is not None:
            return move_str(best_move)

    # Immediate captures: take them.
    capturing = []
    for mv in legal_moves:
        g = capture_count_after(occ_mask, cap_mask, mv)
        if g > 0:
            capturing.append((g, mv))

    if capturing:
        # Prefer double captures, then moves that leave fewer opponent captures.
        best_mv = None
        best_key = None
        for g, mv in capturing:
            nmask, ncmask, _ = apply_move(occ_mask, cap_mask, mv)

            opp_caps = 0
            for idx in all_empty_indices(nmask):
                omv = idx_to_move(idx)
                if capture_count_after(nmask, ncmask, omv) > 0:
                    opp_caps += 1

            key = (g, -opp_caps)
            if best_key is None or key > best_key:
                best_key = key
                best_mv = mv
        return move_str(best_mv)

    # Safe moves: moves that do not create any third side.
    safe = []
    for mv in legal_moves:
        if not creates_third_side(occ_mask, cap_mask, mv):
            # Lower risk score is preferred.
            nmask = occ_mask | (1 << move_to_idx(mv))
            risk = 0
            adjacency = 0
            for br, bc in affected_boxes(mv):
                b = br * 4 + bc
                if not (cap_mask & (1 << b)):
                    s = box_sides_mask(nmask, br, bc)
                    risk += s * s
                    adjacency += 1

            # Slight preference for boundary moves when otherwise equal.
            r, c, d = mv
            boundary = 0
            if d == "H" and (r == 0 or r == 4):
                boundary = 1
            if d == "V" and (c == 0 or c == 4):
                boundary = 1

            safe.append((risk, -boundary, adjacency, mv))

    if safe:
        safe.sort(key=lambda x: (x[0], x[1], x[2]))
        return move_str(safe[0][3])

    # No safe move exists. We must open something.
    # Choose the move that minimizes immediate captures available to the opponent.
    best_mv = None
    best_key = None
    for mv in legal_moves:
        nmask, ncmask, gained = apply_move(occ_mask, cap_mask, mv)

        opp_immediate = 0
        opp_double_potential = 0
        for idx in all_empty_indices(nmask):
            omv = idx_to_move(idx)
            g = capture_count_after(nmask, ncmask, omv)
            if g > 0:
                opp_immediate += 1
                opp_double_potential += g

        # Also prefer opening boxes with fewer already-filled adjacent sides.
        local_damage = 0
        for br, bc in affected_boxes(mv):
            b = br * 4 + bc
            if not (cap_mask & (1 << b)):
                local_damage += box_sides_mask(nmask, br, bc)

        key = (opp_double_potential, opp_immediate, local_damage)
        if best_key is None or key < best_key:
            best_key = key
            best_mv = mv

    if best_mv is not None:
        return move_str(best_mv)

    # Absolute legal fallback.
    return move_str(legal_moves[0])
