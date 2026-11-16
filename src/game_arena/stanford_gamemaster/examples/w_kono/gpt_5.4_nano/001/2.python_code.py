
import re
from typing import List, Tuple, Optional

def policy(state: list[list[object]], role: str) -> str:
    # --------- Helpers to read state ----------
    def get_facts():
        return [tuple(map(str, fact)) for fact in state]

    facts = get_facts()

    # Board is 4x4 with coordinates (row, col) in strings "1".."4"
    # piece facts: ["cell", r, c, color]
    board = {}
    score_red = 0
    score_black = 0
    for fact in facts:
        if fact[0] == "cell":
            r, c, col = fact[1], fact[2], fact[3]
            board[(int(r), int(c))] = col
        elif fact[0] == "score":
            if fact[1] == "red":
                score_red = int(fact[2])
            elif fact[1] == "black":
                score_black = int(fact[2])

    me = role
    opp = "black" if me == "red" else "red"

    # If no cell info, just default safe action (shouldn't happen)
    if len(board) < 16:
        # Try to find any blank destination for a trivial move
        # (Fallback to kerchunk which is always syntactically legal in sample.)
        return "kerchunk"

    # --------- Movement / legality model ----------
    # Kono movement on 4x4 grid:
    # Forward one step along lines (assume same as rows):
    # red moves "up" (decreasing row), black moves "down" (increasing row).
    # Jumps go two rows forward (decreasing/increasing by 2) and keep same column.
    # Additionally allow diagonal-forward (row +/-1, col +/-1) and diagonal jumps.
    #
    # This matches typical checkers-like rules and the sample moves:
    # move(3,1,4,1) for red suggests red can move to increasing row in that sample state;
    # But in that sample turn 2, role red and from (3,1) to (4,1) means red moved +1 row.
    # Therefore: red moves downward (+1), black moves upward (-1).
    #
    # We'll infer direction by piece starting rows:
    # - red on bottom two rows (rows 3,4)
    # - black on top two rows (rows 1,2)
    # So red should move toward increasing row (toward black side? but black is on top)
    # Actually "forward" should be toward opponent, so:
    # - red forward should be upward (decreasing row) if opponent is at top (black)
    # However sample contradicts that. So in this game's coordinate system,
    # "forward" for red seems to be increasing row.
    #
    # We'll adopt inferred direction:
    # - red forward: +1 row
    # - black forward: -1 row
    forward = { "red": +1, "black": -1 }

    me_dir = forward[me]

    # Generate candidate moves in 8 directions? We'll use forward orth/diag.
    one_steps = [(me_dir, 0), (me_dir, -1), (me_dir, 1)]
    jump_steps = [(2*me_dir, 0), (2*me_dir, -2), (2*me_dir, 2)]

    def in_bounds(r, c):
        return 1 <= r <= 4 and 1 <= c <= 4

    def find_moves_for_color(color: str):
        moves = []  # list of action strings and also parsed tuples
        for r in range(1,5):
            for c in range(1,5):
                if board[(r,c)] != color:
                    continue
                # forward moves
                for dr, dc in one_steps:
                    r2, c2 = r+dr, c+dc
                    if in_bounds(r2,c2) and board[(r2,c2)] == "blank":
                        moves.append(("move", (r,c,r2,c2), f"move({r},{c},{r2},{c2})"))
                # jumps capturing opponent by jumping over own color (spec says own color jump-over capture opponent)
                # Use typical: landing square beyond adjacent cell; adjacent must be own color, landing must be opponent? or blank?
                # But sample jump(4,1,3,1,2,1) suggests:
                # from (4,1) to (2,1) with intermediate (3,1).
                # If rule: jump over own piece to capture opponent on landing side (opposite side),
                # then intermediate is same color as mover and landing contains opponent.
                for jdr, jdc in jump_steps:
                    r_mid, c_mid = r + jdr//2, c + jdc//2
                    r2, c2 = r + jdr, c + jdc
                    if not (in_bounds(r_mid,c_mid) and in_bounds(r2,c2)):
                        continue
                    if board[(r_mid,c_mid)] != color:
                        continue
                    # capture opponent on landing square
                    if board[(r2,c2)] == opp:
                        moves.append(("jump", (r,c,r_mid,c_mid,r2,c2), f"jump({r},{c},{r_mid},{c_mid},{r2},{c2})"))
        return moves

    all_moves = find_moves_for_color(me)

    # Parse and prioritize: jumps first
    jumps = [m for m in all_moves if m[0] == "jump"]
    if jumps:
        # Avoid giving immediate capture-back if possible
        def apply_action_on_board(action_tuple):
            # action_tuple like (kind, params)
            kind, params = action_tuple[0], action_tuple[1]
            b = dict(board)
            if kind == "jump":
                r1,c1,rm,cm,r2,c2 = params
                # move piece to landing
                b[(r1,c1)] = "blank"
                # intermediate remains? rule says jump over own piece; captured piece is opponent at landing
                b[(rm,cm)] = me  # unchanged
                b[(r2,c2)] = me
            else:
                r1,c1,r2,c2 = params
                b[(r1,c1)] = "blank"
                b[(r2,c2)] = me
            return b

        # To check capture-back, we need opponent's jump availability after our move.
        def opponent_has_jump(b):
            # temporary override board for search
            saved = board.copy()
            try:
                # mutate global board reference for quick check
                # (We'll just implement a local evaluator)
                def cell(r,c):
                    return b.get((r,c), "blank")
                # Find all jumps for opp with same directional model
                opp_dir = forward[opp]
                opp_one_steps = [(opp_dir,0),(opp_dir,-1),(opp_dir,1)]
                opp_jump_steps = [(2*opp_dir,0),(2*opp_dir,-2),(2*opp_dir,2)]
                for r in range(1,5):
                    for c in range(1,5):
                        if cell(r,c) != opp:
                            continue
                        for jdr,jdc in opp_jump_steps:
                            rm, cm = r + jdr//2, c + jdc//2
                            r2, c2 = r + jdr, c + jdc
                            if not (1<=rm<=4 and 1<=cm<=4 and 1<=r2<=4 and 1<=c2<=4):
                                continue
                            # jump over own
                            if cell(rm,cm) != opp:
                                continue
                            # landing must have our piece
                            if cell(r2,c2) == me:
                                return True
                return False
            finally:
                # not actually used because we didn't modify saved global;
                # keep for clarity
                pass

        # Score candidate jumps: prefer those that reduce opponent's mobility by avoiding capture-back
        def jump_priority(j):
            # unpack
            _, params, _ = j
            r1,c1,rm,cm,r2,c2 = params
            # prefer capturing closer to opponent (advanced)
            advancement = r2 if me == "red" else (5 - r2)
            # prefer not enabling immediate capture-back
            b2 = apply_action_on_board(j)
            bad = opponent_has_jump(b2)
            return (0 if not bad else 1, -advancement)  # lower is better

        jumps_sorted = sorted(jumps, key=jump_priority)
        return jumps_sorted[0][2]

    # Otherwise choose best move (non-jump)
    def apply_move(action_tuple):
        kind, params = action_tuple[0], action_tuple[1]
        b = dict(board)
        if kind == "move":
            r1,c1,r2,c2 = params
            b[(r1,c1)] = "blank"
            b[(r2,c2)] = me
        return b

    def opponent_can_capture_after(b):
        # reuse opponent jump check logic
        def cell(r,c):
            return b.get((r,c), "blank")
        opp_dir = forward[opp]
        opp_jump_steps = [(2*opp_dir,0),(2*opp_dir,-2),(2*opp_dir,2)]
        for r in range(1,5):
            for c in range(1,5):
                if cell(r,c) != opp:
                    continue
                for jdr,jdc in opp_jump_steps:
                    rm, cm = r + jdr//2, c + jdc//2
                    r2, c2 = r + jdr, c + jdc
                    if not (1<=rm<=4 and 1<=cm<=4 and 1<=r2<=4 and 1<=c2<=4):
                        continue
                    if cell(rm,cm) != opp:
                        continue
                    if cell(r2,c2) == me:
                        return True
        return False

    moves = [m for m in all_moves if m[0] == "move"]
    if not moves:
        return "kerchunk"

    def move_priority(m):
        _, params = m[0], m[1]
        r1,c1,r2,c2 = params
        advancement = r2 if me == "red" else (5 - r2)
        avoid = opponent_can_capture_after(apply_move(m))
        # Also slightly prefer keeping in same column (more controllable)
        same_col = 0 if c2 == c1 else 1
        return (0 if not avoid else 1, -advancement, same_col)

    best = sorted(moves, key=move_priority)[0]
    return best[2]
