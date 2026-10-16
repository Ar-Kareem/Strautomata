
import random

def policy(state: list[list[object]], role: str) -> str:
    # --- Parse board ---
    files = "abcdefgh"
    file_to_i = {c: i for i, c in enumerate(files)}

    def in_bounds(x, y):
        return 0 <= x < 8 and 0 <= y < 8

    # Knight deltas
    deltas = [(1, 2), (2, 1), (2, -1), (1, -2),
              (-1, -2), (-2, -1), (-2, 1), (-1, 2)]

    # Collect pieces
    pieces = []  # (x,y, color)
    for fact in state:
        if isinstance(fact, list) and len(fact) >= 4 and fact[0] == "cell":
            f = fact[1]
            r = fact[2]
            c = fact[3]
            if f in file_to_i and isinstance(r, str) and r.isdigit():
                x = file_to_i[f]
                y = int(r) - 1
                if c in ("white", "black"):
                    pieces.append((x, y, c))

    my_color = role
    opp_color = "black" if my_color == "white" else "white"

    my_cells = {(x, y) for x, y, c in pieces if c == my_color}
    opp_cells = {(x, y) for x, y, c in pieces if c == opp_color}

    # If no pieces, return something legal-looking (shouldn't happen)
    if not my_cells:
        return "move(a,1,b,3)"

    # For quick occupancy checks
    occ_my = my_cells
    occ_opp = opp_cells
    occ_all = occ_my | occ_opp

    # --- Generate candidate moves for my pieces ---
    def square_name(x, y):
        return f"{files[x]},{y+1}"

    # Evaluate a move: (capture?, safety?, center/advance)
    # We'll simulate occupancy after the move to detect immediate recapture threats.
    def score_move(sx, sy, tx, ty):
        is_capture = (tx, ty) in occ_opp

        # Center preference: distance to board center (3.5,3.5)
        center_dist = abs(tx - 3.5) + abs(ty - 3.5)
        center_score = -center_dist

        # Advance preference: toward opponent side
        # white moves "up" increasing y; black moves "down" decreasing y
        if my_color == "white":
            advance = ty
        else:
            advance = 7 - ty
        advance_score = advance

        # Immediate threat check: after we move, can opponent capture us back?
        # Opponent could capture the destination square (tx,ty) if it contains our piece.
        # i.e., if any opponent knight can land on (tx,ty) in one move.
        threatened_back = False
        for dx, dy in deltas:
            ax = tx + dx
            ay = ty + dy
            if in_bounds(ax, ay) and (ax, ay) in occ_opp:
                threatened_back = True
                break

        # Also, avoid exposing our piece such that opponent has a capture available on our destination.
        # If threatened_back and we did not capture, heavily penalize; if we captured, smaller penalty.
        safety_penalty = 0
        if threatened_back:
            safety_penalty = 120 if not is_capture else 40

        # Another heuristic: prefer moves that land on squares attacked by opponent? No, avoid.
        # Keep it simple and fast.

        # Capture value: prioritize any capture strongly.
        capture_score = 250 if is_capture else 0

        # Small preference for moving from edge to inside
        edge_penalty = 0
        if sx in (0, 7) or sy in (0, 7):
            edge_penalty = 5

        # Total
        return capture_score + 25 * center_score + 10 * advance_score - safety_penalty - edge_penalty

    candidates = []
    for sx, sy in my_cells:
        for dx, dy in deltas:
            tx, ty = sx + dx, sy + dy
            if not in_bounds(tx, ty):
                continue
            if (tx, ty) in occ_my:
                continue
            # This destination is either empty or opponent piece => legal
            candidates.append((sx, sy, tx, ty))

    # If there are capture moves, consider only those with best score; else consider all.
    best_capture = None
    best_capture_score = -10**18
    any_capture = False
    for sx, sy, tx, ty in candidates:
        if (tx, ty) in occ_opp:
            any_capture = True
            sc = score_move(sx, sy, tx, ty)
            if sc > best_capture_score:
                best_capture_score = sc
                best_capture = (sx, sy, tx, ty)

    if any_capture:
        sx, sy, tx, ty = best_capture
    else:
        # Choose highest scoring candidate; tie-break randomly but deterministically-ish
        best = None
        best_score = -10**18
        for sx, sy, tx, ty in candidates:
            sc = score_move(sx, sy, tx, ty)
            if sc > best_score:
                best_score = sc
                best = (sx, sy, tx, ty)
        sx, sy, tx, ty = best

    # Format: move(fromFile,fromRank,toFile,toRank)
    from_sq = (files[sx], sy + 1)
    to_sq = (files[tx], ty + 1)

    # Convert to syntax move(a,1,b,3)
    return f"move({from_sq[0]},{from_sq[1]},{to_sq[0]},{to_sq[1]})"
