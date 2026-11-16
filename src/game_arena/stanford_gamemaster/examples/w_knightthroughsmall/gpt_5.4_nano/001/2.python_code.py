
from __future__ import annotations

def policy(state: list[list[object]], role: str) -> str:
    # Board is 6x6 with columns a-f and rows 1-6.
    cols = ["a", "b", "c", "d", "e", "f"]
    col_to_i = {c: i for i, c in enumerate(cols, start=1)}  # 1..6
    i_to_col = {i: c for c, i in col_to_i.items()}

    my = role
    opp = "black" if role == "white" else "white"

    def parse_cells():
        pieces = []
        for fact in state:
            if len(fact) >= 4 and fact[0] == "cell":
                col, row, who = fact[1], fact[2], fact[3]
                if who in ("white", "black"):
                    pieces.append((col_to_i[col], int(row), who))
        return pieces

    pieces = parse_cells()
    occupied = {(x, y): who for (x, y, who) in pieces}

    my_cells = [(x, y) for (x, y, who) in pieces if who == my]

    # Knight deltas (dx,dy) where dx in {-2,-1,1,2} dy accordingly
    knight_deltas = [
        (2, 1), (2, -1), (-2, 1), (-2, -1),
        (1, 2), (1, -2), (-1, 2), (-1, -2)
    ]

    # Forward-only constraint: white moves to increasing row, black to decreasing row
    def is_forward(dy: int) -> bool:
        return dy > 0 if my == "white" else dy < 0

    def in_bounds(x: int, y: int) -> bool:
        return 1 <= x <= 6 and 1 <= y <= 6

    def legal_moves_from(x: int, y: int):
        moves = []
        for dx, dy in knight_deltas:
            if not is_forward(dy):
                continue
            nx, ny = x + dx, y + dy
            if not in_bounds(nx, ny):
                continue
            if (nx, ny) in occupied and occupied[(nx, ny)] == my:
                continue  # can't land on own piece
            # capture allowed
            moves.append((nx, ny))
        return moves

    # Win condition: first to reach opposite side
    def is_win_position(x: int, y: int, who: str) -> bool:
        return (who == "white" and y == 6) or (who == "black" and y == 1)

    # Evaluate a move for my.
    def evaluate_move(srcx, srcy, dstx, dsty):
        # Simulate occupation after move
        sim_occ = dict(occupied)
        # Remove captured piece at destination if any
        if (dstx, dsty) in sim_occ:
            del sim_occ[(dstx, dsty)]
        # Move piece
        del sim_occ[(srcx, srcy)]
        sim_occ[(dstx, dsty)] = my

        # Immediate win
        if is_win_position(dstx, dsty, my):
            return 10_000_000

        # If opponent has immediate win next, heavily penalize
        # Determine opponent's possible moves from their pieces
        opp_pieces = [(x, y) for (x, y), who in sim_occ.items() if who == opp]
        opp_forward = (opp == "white")
        def opp_is_forward(dy: int) -> bool:
            return dy > 0 if opp_forward else dy < 0

        for ox, oy in opp_pieces:
            for dx, dy in knight_deltas:
                if not opp_is_forward(dy):
                    continue
                nx, ny = ox + dx, oy + dy
                if not in_bounds(nx, ny):
                    continue
                # can't capture own
                if (nx, ny) in sim_occ and sim_occ[(nx, ny)] == opp:
                    continue
                # landing allowed
                if is_win_position(nx, ny, opp):
                    return -10_000_000

        # Heuristic: prefer more advanced progress and center-ish
        # Progress term
        if my == "white":
            progress = dsty
        else:
            progress = 7 - dsty  # closer to row 1 means larger value
        progress_score = progress * 1000

        # Distance to opponent's edge (same as progress) and avoid staying behind
        src_progress = srcy if my == "white" else 7 - srcy
        delta = progress - src_progress
        advance_score = delta * 600

        # Capture bonus (if we capture something)
        capture_bonus = 0
        if (dstx, dsty) in occupied and occupied[(dstx, dsty)] == opp:
            capture_bonus = 2500

        # Slight preference for moving toward center columns
        center = 3.5
        center_score = -abs(dstx - center) * 40

        # Mild piece-safety: don't allow easy immediate win by opponent if possible
        # (already checked immediate win, so just add small term for not being on very vulnerable squares)
        safety = 0

        return progress_score + advance_score + capture_bonus + center_score + safety

    # Generate candidate moves, choose best
    best_action = None
    best_val = None

    for sx, sy in my_cells:
        for dx, dy in legal_moves_from(sx, sy):
            val = evaluate_move(sx, sy, dx, dy)
            if best_val is None or val > best_val:
                best_val = val
                best_action = (sx, sy, dx, dy)

    # Fallback: pick the first legal move deterministically
    if best_action is None:
        for sx, sy in my_cells:
            lm = legal_moves_from(sx, sy)
            if lm:
                dx, dy = lm[0]
                best_action = (sx, sy, dx, dy)
                break

    # Convert to move(col1,row1,col2,row2)
    sx, sy, dx, dy = best_action
    return f"move({i_to_col[sx]},{sy},{i_to_col[dx]},{dy})"
