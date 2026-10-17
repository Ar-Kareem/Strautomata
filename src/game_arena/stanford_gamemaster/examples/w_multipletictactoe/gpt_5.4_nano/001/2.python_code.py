
import math
from typing import List, Tuple, Optional

def policy(state: list[list[object]], role: str) -> str:
    # Parse state into a mapping from (board_r, board_c, cell_r, cell_c) -> mark
    # Observed proposition format in examples:
    # ["cell", board_r, board_c, cell_r, cell_c, content]
    # where content is 'b' (blank) or 'x'/'o'.
    board = {}  # (br,bc,cr,cc) -> 'b'/'x'/'o'
    control = None
    for fact in state:
        if not fact:
            continue
        if fact[0] == "control" and len(fact) >= 2:
            control = fact[1]
        if fact[0] == "cell" and len(fact) >= 6:
            br, bc, cr, cc, cont = fact[1], fact[2], fact[3], fact[4], fact[5]
            board[(int(br), int(bc), int(cr), int(cc))] = cont

    # Determine which mark we are placing
    my = role.strip()
    opp = "o" if my == "x" else "x"

    # Middle board is indexed (2,2) in the examples
    MB = (2, 2)

    def middle_cell(cr: int, cc: int) -> str:
        return board.get((MB[0], MB[1], cr, cc), "b")

    # Generate legal moves from the given state:
    # A move mark(br,bc,cr,cc) is legal if corresponding cell is blank ('b').
    # We don't know turn legality beyond control, but the requested action must be legal
    # for the role; control indicates who is to move in examples.
    # We'll restrict to any blank cells; if control doesn't match, still should not happen.
    blanks = []
    for (br, bc, cr, cc), cont in board.items():
        if cont == "b":
            blanks.append((br, bc, cr, cc))
    if not blanks:
        # Shouldn't happen; but return a dummy legal-looking move if needed
        return "mark(1,1,1,1)"

    # If middle board has blanks, search there first; that's where winning matters.
    mb_blanks = [(cr, cc) for cr in range(1,4) for cc in range(1,4) if middle_cell(cr, cc) == "b"]

    lines = [
        [(1,1),(1,2),(1,3)],
        [(2,1),(2,2),(2,3)],
        [(3,1),(3,2),(3,3)],
        [(1,1),(2,1),(3,1)],
        [(1,2),(2,2),(3,2)],
        [(1,3),(2,3),(3,3)],
        [(1,1),(2,2),(3,3)],
        [(1,3),(2,2),(3,1)],
    ]

    def winner_if(place: Tuple[int,int], who: str) -> bool:
        cr, cc = place
        # check all lines containing (cr,cc)
        for a,b,c in lines:
            line = [a,b,c]
            if (cr,cc) not in line:
                continue
            ok = True
            for (lr, lc) in line:
                if (lr,lc) == (cr,cc):
                    if who != who:
                        ok = False
                else:
                    if middle_cell(lr,lc) != who:
                        ok = False
            if ok:
                return True
        return False

    def would_win(place: Tuple[int,int], who: str) -> bool:
        cr, cc = place
        for line in lines:
            if (cr,cc) not in line:
                continue
            if all((middle_cell(r,c) == who) if (r,c)!=(cr,cc) else True for (r,c) in line):
                # But above is wrong: it doesn't ensure placed cell equals who (always true).
                # We just need check that all other cells in line are who, and placed cell is blank.
                ok = True
                for (r,c) in line:
                    if (r,c) == (cr,cc):
                        if middle_cell(cr,cc) != "b":
                            ok = False
                    else:
                        if middle_cell(r,c) != who:
                            ok = False
                if ok:
                    return True
        return False

    def count_two_in_row(who: str) -> int:
        # Score potential lines with exactly two who and one blank (no opponent)
        opp_here = opp
        score = 0
        for line in lines:
            vals = []
            for (r,c) in line:
                v = middle_cell(r,c)
                vals.append(v)
            if opp_here in vals:
                continue
            if vals.count(who) == 2 and vals.count("b") == 1:
                score += 1
        return score

    def count_block_threats(who: str) -> int:
        # Threats by who on middle board: exactly two who and one blank
        score = 0
        for line in lines:
            vals = [middle_cell(r,c) for (r,c) in line]
            if who in vals and opp not in vals:
                if vals.count(who) == 2 and vals.count("b") == 1:
                    score += 1
        return score

    # 1) Win if possible on middle board
    for (cr, cc) in mb_blanks:
        if would_win((cr,cc), my):
            return f"mark(2,2,{cr},{cc})"

    # 2) Block opponent immediate win on middle board
    for (cr, cc) in mb_blanks:
        if would_win((cr,cc), opp):
            return f"mark(2,2,{cr},{cc})"

    # 3) Otherwise choose best heuristic on middle board
    def heuristic_move(cr: int, cc: int) -> float:
        # Prefer center, then corners, then edges
        pos_w = {(2,2): 5.0, (1,1): 4.0, (1,3): 4.0, (3,1): 4.0, (3,3): 4.0,
                 (1,2): 2.5, (2,1): 2.5, (2,3): 2.5, (3,2): 2.5}
        base = pos_w.get((cr,cc), 1.0)

        # Simulate: set that cell to my for scoring
        orig = middle_cell(cr,cc)
        # temporarily set
        board[(MB[0],MB[1],cr,cc)] = my

        # measure: how many lines become strong
        twos = count_two_in_row(my)
        opp_twos = count_block_threats(opp)  # opponent threats after our move (they may reduce)
        # Also reward immediate creation of "fork-like" (multiple threats)
        # Score: our twos - opponent twos (more opponent threats is bad)
        sim = twos * 3.0 - opp_twos * 2.0

        # restore
        board[(MB[0],MB[1],cr,cc)] = orig
        return base + sim

    if mb_blanks:
        best = None
        bestv = -1e9
        for (cr, cc) in mb_blanks:
            v = heuristic_move(cr, cc)
            if v > bestv:
                bestv = v
                best = (cr, cc)
        return f"mark(2,2,{best[0]},{best[1]})"

    # 4) If middle board full, fall back to any blank with a light preference
    # (since game score only middle board, this should be rare; still must be legal)
    def general_pref(m):
        br, bc, cr, cc = m
        # prefer central cells of the chosen board (2,2 within sub-board)
        return (cr == 2 and cc == 2, (cr in (1,3) and cc in (1,3)), -abs(cr-2)-abs(cc-2))

    move = sorted(blanks, key=general_pref, reverse=True)[0]
    return f"mark({move[0]},{move[1]},{move[2]},{move[3]})"
