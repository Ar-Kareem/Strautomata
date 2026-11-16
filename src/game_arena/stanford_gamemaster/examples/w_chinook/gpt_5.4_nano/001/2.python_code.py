
import re
from typing import List, Tuple, Optional, Set

def policy(state: list[list[object]], role: str) -> str:
    """
    Stanford GameMaster 'chinook' policy.
    Returns a single legal move string: move(x1,y1,x2,y2) or jump(x1,y1,x2,y2,x3,y3).
    """
    # ---------- Helpers to parse ----------
    def parse_cell_facts(st: list[list[object]]):
        pieces = []
        scores = {}
        control = set()
        step = None
        for fact in st:
            if not fact:
                continue
            t = fact[0]
            if t == "cell":
                # ["cell", col, row, color]
                pieces.append((fact[1], fact[2], fact[3]))
            elif t == "score":
                scores[fact[1]] = fact[2]
            elif t == "control":
                control.add(fact[1])
            elif t == "step":
                step = fact[1]
        return pieces, scores, control, step

    pieces, scores, control, step = parse_cell_facts(state)

    # Board mapping: 4 rows (a..d), 8 cols (1..8) with wrap-around.
    cols = ["1","2","3","4","5","6","7","8"]
    rows = ["a","b","c","d"]
    col_to_i = {c:i for i,c in enumerate(cols)}
    row_to_i = {r:i for i,r in enumerate(rows)}
    i_to_col = {i:c for c,i in col_to_i.items()}
    i_to_row = {i:r for r,i in row_to_i.items()}

    # target rows: 3 rows across from starting positions.
    # In typical 4x8 chinook, red starts at rows a..c? but from description:
    # "red player's pieces are positioned on the odd squares, and the blue ... even squares"
    # We don't have explicit start rows, so we infer target by color movement direction.
    # Red moves up the board. We'll treat "up" as row index decreasing modulo 4.
    # Then red target is the 3 rows "at the top" (row index -1,-2,-3 from red movement start),
    # equivalently the rows with minimal distance in the up direction from current.
    # Likewise blue moves down, target at bottom.
    #
    # To robustly handle, we define targets as:
    # red_target_rows = {0,1,2} if up is decreasing from initial red side (assume red starts at d..b?).
    # But better: compute distance-to-target by stepping up/down; since board is small,
    # we can just define target as the 3 rows that are furthest in the movement direction
    # from the opponent start; i.e., rows with smallest remaining steps to reach "other side".
    #
    # We'll assume red targets are rows 'a','b','c' when moving up (d is start side), and blue targets are 'b','c','d' when moving down.
    # This matches standard orientation where opponent side is across.
    red_target = { "a","b","c" }
    blue_target = { "b","c","d" }

    # Build occupancy
    occ = {}  # (row_i, col_i) -> color
    for r, c, color in pieces:
        occ[(row_to_i[r], col_to_i[c])] = color

    my_color = role
    opp_color = "blue" if role == "red" else "red"

    # Movement directions:
    # Red advances "up": row_i - 1 (with wrap), Blue advances "down": row_i + 1 (wrap).
    # Diagonal: also col changes by +-1 (wrap).
    def wrap(x, mod):
        return x % mod

    def in_bounds(r_i, c_i):
        return True  # wrap-around so always.

    # Legal move generation:
    # Per examples, action formats:
    # move(col1,row1,col2,row2) where first two args correspond to from cell (col,row?) Actually examples: move(a,3,b,4)
    # Here first token is column letter and second is row number; so move(from_col, from_rownum, to_col, to_rownum)
    # i.e. move(rowLetter, colNumber, rowLetter, colNumber) in their naming.
    #
    # We'll treat: x = row letter, y = column number.
    def cell_to_arg(row_i, col_i):
        return (i_to_row[row_i], i_to_col[col_i])

    # Red can move to empty diagonal up squares OR jump over its own pieces.
    # Blue similarly down.
    #
    # From examples, jumps are of form jump(b,7,a,6,d,5) = from(b,7) over(a,6) land(d,5).
    # That implies:
    # from at (row=b, col=7) to mid at (row=a, col=6) to landing at (row=d, col=5)
    # Row change: b->a (-1), landing a->d (+1 wrap) corresponds to jump direction continuing.
    # Col change: 7->6 (-1), 6->5 (-1).
    #
    # So jump distance is 2 steps in the same diagonal direction.
    # Mid cell is exactly one step away.
    #
    # We'll allow jumps when the mid cell contains MY color (per description) and landing is empty.
    def generate_moves():
        moves = []
        for (r_i, c_i), color in occ.items():
            if color != my_color:
                continue
            dir_r = -1 if my_color == "red" else 1
            # Two diagonals: col +/-1
            for dc in (-1, 1):
                r1 = wrap(r_i + dir_r, 4)
                c1 = wrap(c_i + dc, 8)
                # Simple move to empty
                if (r1, c1) not in occ:
                    fr, fc = cell_to_arg(r_i, c_i)
                    tr, tc = cell_to_arg(r1, c1)
                    moves.append(f"move({fr},{fc},{tr},{tc})")
                # Jump over own piece (mid) to empty landing
                r2 = wrap(r_i + 2*dir_r, 4)
                c2 = wrap(c_i + 2*dc, 8)
                if (r1, c1) in occ and occ[(r1, c1)] == my_color and (r2, c2) not in occ:
                    fr, fc = cell_to_arg(r_i, c_i)
                    mr, mc = cell_to_arg(r1, c1)
                    lr, lc = cell_to_arg(r2, c2)
                    # jump(from, mid, land) but in syntax: jump(x1,y1,x2,y2,x3,y3)
                    moves.append(f"jump({fr},{fc},{mr},{mc},{lr},{lc})")
        return moves

    legal_moves = generate_moves()
    if not legal_moves:
        # Fallback: shouldn't happen; return some move from state if possible.
        # Try any generated again (should be non-empty). If still empty, arbitrary.
        return "move(a,1,a,2)"

    # ---------- Heuristic evaluation ----------
    def successor_after(move_str: str):
        # Apply move to occ (copy) and return new occ.
        new_occ = dict(occ)
        # Determine move type
        if move_str.startswith("move"):
            nums = re.findall(r"move\(([^)]+)\)", move_str)[0].split(",")
            fr, fc, tr, tc = nums[0], nums[1], nums[2], nums[3]
            r_i, c_i = row_to_i[fr], col_to_i[fc]
            r_j, c_j = row_to_i[tr], col_to_i[tc]
            color = new_occ.pop((r_i, c_i))
            new_occ[(r_j, c_j)] = color
        else:
            nums = re.findall(r"jump\(([^)]+)\)", move_str)[0].split(",")
            fr, fc, mr, mc, tr, tc = nums[0], nums[1], nums[2], nums[3], nums[4], nums[5]
            r_i, c_i = row_to_i[fr], col_to_i[fc]
            r_m, c_m = row_to_i[mr], col_to_i[mc]
            r_j, c_j = row_to_i[tr], col_to_i[tc]
            color = new_occ.pop((r_i, c_i))
            # mid not removed (jump over own pieces)
            new_occ[(r_j, c_j)] = color
        return new_occ

    def score_occ(new_occ):
        # Higher is better for my_color.
        # Reward pieces on target rows; reward proximity advancement.
        total = 0
        for (r_i, c_i), color in new_occ.items():
            if color != my_color:
                continue
            row_letter = i_to_row[r_i]
            # target reward
            if (my_color == "red" and row_letter in red_target) or (my_color == "blue" and row_letter in blue_target):
                total += 50
            # distance-to-target along movement direction:
            # for red, "up": decreasing row index; for blue, increasing.
            # compute minimal steps along that direction to reach any target row.
            if my_color == "red":
                # target rows should be "ahead" by moving -1
                best = 10
                for tr in red_target:
                    t_i = row_to_i[tr]
                    # steps k >=0 such that wrap(r_i - k)=t_i => r_i - k ≡ t_i => k ≡ r_i - t_i
                    k = (r_i - t_i) % 4
                    best = min(best, k)
                # smaller best => closer
                total += (6 - best)  # 0..6
            else:
                best = 10
                for tr in blue_target:
                    t_i = row_to_i[tr]
                    # steps k: r_i + k ≡ t_i
                    k = (t_i - r_i) % 4
                    best = min(best, k)
                total += (6 - best)

        # slight penalty for giving opponent more target pieces
        opp_target = 0
        for (r_i, c_i), color in new_occ.items():
            if color != opp_color:
                continue
            row_letter = i_to_row[r_i]
            if (opp_color == "red" and row_letter in red_target) or (opp_color == "blue" and row_letter in blue_target):
                opp_target += 1
        total -= 5 * opp_target
        return total

    best_move = None
    best_val = None

    for m in legal_moves:
        new_occ = successor_after(m)
        val = score_occ(new_occ)
        if best_val is None or val > best_val or (val == best_val and m < best_move):
            best_val = val
            best_move = m

    return best_move
