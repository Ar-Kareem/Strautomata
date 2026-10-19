
import re
from typing import List, Tuple, Optional

# Board letters used in this game are three 3x8 boards; examples show a,b,c.
FILES = ["a", "b", "c", "d"]
BOARDS = ["a", "b", "c"]

def _parse_state(state: List[List[object]]):
    # Returns dict: role -> set((board,file,row_int))
    pieces = {"white": set(), "black": set()}
    control = None
    for fact in state:
        if not fact:
            continue
        if fact[0] == "control" and len(fact) >= 2:
            control = fact[1]
        if fact[0] == "cell" and len(fact) >= 5:
            board, file_, row_s, role = fact[1], fact[2], fact[3], fact[4]
            try:
                row = int(row_s)
            except:
                continue
            if role in pieces and board in BOARDS and file_ in FILES:
                pieces[role].add((board, file_, row))
    return pieces, control

def _knight_forward_targets(board: str, file_: str, row: int, role: str) -> List[Tuple[str,str,int]]:
    # Knight moves on 4 columns (a-d), forward only:
    # If white moves "forward" increasing row. If black moves "forward" decreasing row.
    # Knight deltas: (±2, ±1) in (file,row). We'll treat row as vertical.
    file_idx = FILES.index(file_)
    forward_sign = 1 if role == "white" else -1

    targets = []
    # (delta_file, delta_row)
    deltas = [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]
    for df, dr in deltas:
        nf_idx = file_idx + df
        if 0 <= nf_idx < len(FILES):
            # Enforce forward-only: resulting row must be strictly further in the forward direction
            nr = row + dr * forward_sign//abs(forward_sign) if False else row + dr*forward_sign
            # The above line is unnecessary; keep simple below.
    # Let's implement correctly: dr in deltas refers to row change; forward-only means
    # for white, new_row > row; for black, new_row < row. Just filter accordingly.
    targets = []
    for df, dr in deltas:
        nf_idx = file_idx + df
        if 0 <= nf_idx < len(FILES):
            nr = row + dr  # dr already in "row direction" relative to white baseline
            # Determine forward direction by role:
            if role == "white":
                if nr <= row:
                    continue
            else:
                if nr >= row:
                    continue
            # rows are 1..8
            if 1 <= nr <= 8:
                targets.append((board, FILES[nf_idx], nr))
    return targets

def _generate_legal_moves_for_role(pieces: set, role: str, opp_pieces: set) -> List[Tuple[str,str,int,str,str,int]]:
    # Returns list of move tuples: (from_board, from_file, from_row, to_board, to_file, to_row)
    moves = []
    # In examples, destination board can differ? But actions shown:
    # move(a,a,1,b,3) moves board a->b and file a->a, row 1->3.
    # So there is a "board" transition too. Likely rule: knight can move across boards according to
    # some mapping, but we don't have enough to infer precisely.
    #
    # However, in all given example moves, the board letter changes consistent with moving "forward"
    # across the 3 boards? Empirically:
    # move(a,a,1,b,3): board a->b, row 1->3 (increase by +2)
    # move(b,a,1,b,3): board b->b, row 1->3 (increase +2)
    #
    # Because board transition is underspecified, we'll allow destination board to be any of the three.
    # This will risk illegal moves if board transitions are constrained, but we need legality.
    #
    # Better inference: the knight moves in a 2D grid; "board" is x-coordinate among three boards,
    # while "file" is y-coordinate among four columns. Then a move from (board,file,row) uses df over
    # (board,file) in a knight pattern. We can't fully reconstruct mapping between deltas and (board,file).
    #
    # Yet sample indicates board changes happen only when df=0 in files? Not reliable.
    #
    # Practical approach: attempt to infer by treating (board,file) as 2D with dimensions 3 and 4.
    # Map board index as x (0..2), file index as y (0..3). Then apply knight moves in (x,y) plane,
    # while row always changes by forward-only rule using remaining delta.
    #
    # But knight in this game likely moves in (file,row) only, not across boards; boards may represent
    # segments along the forward axis? In that case forward progress corresponds to board change.
    #
    # For "multipleknightthrough": 3 boards stacked in the forward direction. So forward-only should mean
    # moving to a later row on possibly later board segments.
    #
    # Therefore, treat the actual forward coordinate as (board,row) along a single 12-long track split into 3 boards.
    # If so, mapping between (board,row) to a global row and back could explain board transitions.
    #
    # Assume each board has rows 1..8; but examples keep row within 1..8 while board letter changes.
    # That suggests global forward coordinate increments by 1 corresponds to either row increment or board change.
    #
    # Given uncertainty, simplest legality-safe method:
    # - only output moves where (from_board,from_file,from_row) exists
    # - and destination square also contains no "cell" absence? (We don't have empty squares enumeration)
    # So we must rely on legality format, not occupancy.
    #
    # In this arena, legality is typically checked purely by game rules, so we must be correct.
    #
    # From examples: move(a,a,1,b,3) suggests from (a,a,1) to (b,a,3): file unchanged, row +2, board +1.
    # That matches a knight delta of (+1 in board dimension, +2 in row) with no file delta.
    #
    # Another example: move(a,a,2,b,4) would be consistent with board +1, row +2.
    #
    # We will model moves as knight on 3x4 (board,file) where "row" is independent forward offset by ±?:
    # We'll instead model the knight move as in 3D with deltas:
    # - in the horizontal 2D plane (board,file): knight move (±1,±2) or (±2,±1)
    # - in the vertical row: exactly ±2? But examples show row changes by +2 when board changes by +1.
    #
    # To get something consistent: use standard knight in (board,file) plane and change row by +2 (white) or -2 (black).
    # Plus if the knight delta in (board,file) uses different patterns, row could change by +1 or +2.
    #
    # We'll adopt: row changes by +2 for any move that advances forward.
    #
    # Specifically: use knight moves in the (board_index,file_index) plane, then set new_row = row + forward_sign*2.
    #
    # This will likely match given trajectories where row increments by 2.
    forward_sign = 1 if role == "white" else -1
    board_idx = BOARDS.index  # type: ignore
    bsz = len(BOARDS)
    fsz = len(FILES)

    deltas_xy = [(1,2),(1,-2),(-1,2),(-1,-2),(2,1),(2,-1),(-2,1),(-2,-1)]
    for (fb, ff, fr) in pieces:
        fi = FILES.index(ff)
        bi = BOARDS.index(fb)
        for db, df in deltas_xy:
            nb = bi + db
            nf = fi + df
            if 0 <= nb < bsz and 0 <= nf < fsz:
                nr = fr + forward_sign*2
                if 1 <= nr <= 8:
                    tb = BOARDS[nb]
                    tf = FILES[nf]
                    # can't capture own piece
                    if (tb, tf, nr) in pieces:
                        continue
                    moves.append((fb, ff, fr, tb, tf, nr))
    return moves

def _move_string(m: Tuple[str,str,int,str,str,int]) -> str:
    fb, ff, fr, tb, tf, tr = m
    return f"move({fb},{ff},{fr},{tb},{tf},{tr})"

def policy(state: List[List[object]], role: str) -> str:
    pieces, _ = _parse_state(state)
    my_pieces = pieces.get(role, set())
    opp_role = "black" if role == "white" else "white"
    opp_pieces = pieces.get(opp_role, set())

    # Goal conditions: white reaches row 8 on board b; black reaches row 1 on board b
    goal_row = 8 if role == "white" else 1
    goal_board = "b"

    legal_moves = _generate_legal_moves_for_role(my_pieces, role, opp_pieces)

    # If our move generation mismatches legality, fallback: try a known pattern from examples:
    # move(a,a,1,b,3) -> generalize: (board,file,row) -> (next_board,file,row+2) for white and reverse for black.
    if not legal_moves:
        forward = 2 if role == "white" else -2
        next_board_idx_delta = 1 if role == "white" else -1
        for (fb, ff, fr) in my_pieces:
            bi = BOARDS.index(fb)
            nb = bi + next_board_idx_delta
            if 0 <= nb < len(BOARDS):
                tr = fr + forward
                if 1 <= tr <= 8:
                    tb = BOARDS[nb]
                    if (tb, ff, tr) in my_pieces:
                        continue
                    legal_moves = [(fb, ff, fr, tb, ff, tr)]
                    break
        if not legal_moves:
            # As last resort (still must be legal), pick any existing piece and attempt no-op? not allowed.
            # We'll output the first syntactically plausible move from a piece.
            for (fb, ff, fr) in my_pieces:
                # try staying on same file with row+2
                tr = fr + (2 if role == "white" else -2)
                if 1 <= tr <= 8:
                    tb = fb
                    legal_moves = [(fb, ff, fr, tb, ff, tr)]
                    break

    # Rank moves
    def score(m):
        fb, ff, fr, tb, tf, tr = m
        # winning
        if tb == goal_board and tr == goal_row:
            return (10**9, 0, 0)
        # advancement
        adv = tr - fr if role == "white" else fr - tr
        # prefer captures (if any)
        cap = 1 if (tb, tf, tr) in opp_pieces else 0
        # avoid moving into occupied by opponent? prefer capture instead.
        return (adv, cap, 0)

    best = max(legal_moves, key=score)
    return _move_string(best)
