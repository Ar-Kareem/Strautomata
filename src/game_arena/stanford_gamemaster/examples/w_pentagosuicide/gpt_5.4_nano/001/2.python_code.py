
import random
import itertools
from typing import List, Tuple, Optional

# ---------- Parsing helpers ----------

def _get_fact(state, pred):
    for f in state:
        if isinstance(f, list) and f and pred(f):
            return f
    return None

def _role_from_control(state) -> Optional[str]:
    for f in state:
        if isinstance(f, list) and len(f) == 2 and f[0] == "control":
            return f[1]
    return None

def _phase_from_state(state) -> Optional[str]:
    # typically ["phase","place"] or ["phase","rotate"]
    for f in state:
        if isinstance(f, list) and len(f) == 2 and f[0] == "phase":
            return f[1]
    return None

def _board_from_state(state) -> List[List[Optional[str]]]:
    # board coords in propositions are 1..6
    board = [[None for _ in range(6)] for _ in range(6)]
    for f in state:
        if isinstance(f, list) and len(f) == 5 and f[0] == "cellholds":
            _, r, c, _maybe_cellidx, color = f
            try:
                r_i = int(r) - 1
                c_i = int(c) - 1
            except:
                continue
            if 0 <= r_i < 6 and 0 <= c_i < 6:
                board[r_i][c_i] = color
    return board

def _other(player: str) -> str:
    return "black" if player == "red" else "red"

# ---------- Game mechanics ----------

def _empty_cells(board: List[List[Optional[str]]]) -> List[Tuple[int,int]]:
    res = []
    for r in range(6):
        for c in range(6):
            if board[r][c] is None:
                res.append((r,c))
    return res

def _quadrant_of(r: int, c: int) -> int:
    # r,c are 0..5
    # quadrants: 1:(0-2,0-2), 2:(0-2,3-5), 3:(3-5,0-2), 4:(3-5,3-5)
    if r < 3 and c < 3:
        return 1
    if r < 3 and c >= 3:
        return 2
    if r >= 3 and c < 3:
        return 3
    return 4

def _rotate_quadrant(board: List[List[Optional[str]]], q: int, clockwise: bool) -> List[List[Optional[str]]]:
    # returns new board after rotation
    newb = [row[:] for row in board]
    if q == 1:
        r0,c0 = 0,0
    elif q == 2:
        r0,c0 = 0,3
    elif q == 3:
        r0,c0 = 3,0
    else:
        r0,c0 = 3,3

    # extract 3x3
    temp = [[board[r0+i][c0+j] for j in range(3)] for i in range(3)]
    if clockwise:
        # new[i][j] = temp[2-j][i]
        for i in range(3):
            for j in range(3):
                newb[r0+i][c0+j] = temp[2-j][i]
    else:
        # counterclockwise: new[i][j] = temp[j][2-i]
        for i in range(3):
            for j in range(3):
                newb[r0+i][c0+j] = temp[j][2-i]
    return newb

# ---------- Evaluation ----------

DIRS = [(0,1),(1,0),(1,1),(1,-1)]

def _has_five_in_row(board: List[List[Optional[str]]], player: str) -> bool:
    # check any length-5 line among all directions; since board can have >5,
    # we just need to detect any 5 contiguous positions.
    for r in range(6):
        for c in range(6):
            if board[r][c] != player:
                continue
            for dr,dc in DIRS:
                # 5 cells start at (r,c) going dr,dc; ensure within bounds
                end_r = r + dr*4
                end_c = c + dc*4
                if 0 <= end_r < 6 and 0 <= end_c < 6:
                    ok = True
                    for k in range(5):
                        rr = r + dr*k
                        cc = c + dc*k
                        if board[rr][cc] != player:
                            ok = False
                            break
                    if ok:
                        return True
    return False

def _line_counts_for_player(board: List[List[Optional[str]]], player: str) -> int:
    # Count number of 5-contiguous segments that are "potentially" good for player:
    # segment is all player or empty/own? In pentago, interference by opponent matters.
    # We'll use: segment contributes 1,2,4 based on number of player marks and no opponent marks.
    opponent = _other(player)
    score = 0
    for r in range(6):
        for c in range(6):
            if board[r][c] == opponent:
                continue
            for dr,dc in DIRS:
                end_r = r + dr*4
                end_c = c + dc*4
                if 0 <= end_r < 6 and 0 <= end_c < 6:
                    cells = [board[r+dr*k][c+dc*k] for k in range(5)]
                    if opponent in cells:
                        continue
                    cnt = sum(1 for x in cells if x == player)
                    if cnt == 5:
                        score += 100000
                    elif cnt == 4:
                        score += 2000
                    elif cnt == 3:
                        score += 250
                    elif cnt == 2:
                        score += 40
                    elif cnt == 1:
                        score += 5
                    else:
                        pass
    return score

def _evaluate(board: List[List[Optional[str]]], me: str) -> int:
    # Large win/loss signals
    opp = _other(me)
    if _has_five_in_row(board, me):
        return 100000000
    if _has_five_in_row(board, opp):
        return -100000000
    # Heuristic based on potential segments
    return _line_counts_for_player(board, me) - _line_counts_for_player(board, opp)

def _best_rotate(board: List[List[Optional[str]]], me: str) -> Tuple[int, bool, int]:
    best = None
    best_score = -10**18
    for q in [1,2,3,4]:
        for cw in [True, False]:
            nb = _rotate_quadrant(board, q, cw)
            sc = _evaluate(nb, me)
            if sc > best_score:
                best_score = sc
                best = (q, cw)
    return best[0], best[1], best_score

# ---------- Policy ----------

def policy(state: list[list[object]], role: str) -> str:
    board = _board_from_state(state)
    phase = _phase_from_state(state)
    if phase is None:
        # default to place if unknown
        phase = "place"
    control = _role_from_control(state)
    me = role if control is None else control
    # Some arenas may call policy with correct role; still, use role for scoring.
    # If mismatch occurs, assume it's still our turn when called.
    me = role

    empties = _empty_cells(board)

    # If it's our move and phase is place, generate best place.
    if phase == "place":
        if not empties:
            # board full, no legal place; fallback pick any (shouldn't happen)
            return "place(1,1,1)"
        # Candidate limit: prioritize empties that touch existing stones to reduce work.
        existing = [(r,c) for r in range(6) for c in range(6) if board[r][c] is not None]
        neighbor_set = set()
        for r,c in existing:
            for dr in (-1,0,1):
                for dc in (-1,0,1):
                    rr,cc = r+dr,c+dc
                    if 0 <= rr < 6 and 0 <= cc < 6 and board[rr][cc] is None:
                        neighbor_set.add((rr,cc))
        candidates = list(neighbor_set) if neighbor_set else empties

        # Quick tactical: if any placement immediately wins, do it.
        for (r,c) in candidates:
            nb = [row[:] for row in board]
            nb[r][c] = me
            if _has_five_in_row(nb, me):
                q = _quadrant_of(r,c)
                # after placement, must rotate some quadrant; choose rotation maximizing our outcome
                rq, cw, _ = _best_rotate(nb, me)
                return f"place({r+1},{c+1},{rq})"
        # Otherwise evaluate each placement assuming we then rotate optimally
        best_action = None
        best_score = -10**18
        opp = _other(me)

        # If opponent can already win next rotation after our placement? Hard to foresee fully.
        # We'll do: score = our best-after-rotation - opponent's best-after-rotation (with our immediate rotate choice).
        # This is strong enough for single-ply.
        for (r,c) in candidates:
            nb = [row[:] for row in board]
            nb[r][c] = me

            # Our best rotation
            q_me, cw_me, sc_me = _best_rotate(nb, me)

            # For robustness, also compute opponent best response after their next placement is unknown.
            # We just penalize if opponent already has five after our chosen rotation.
            # (We can emulate best for opponent by checking max over rotations for opponent.)
            best_opp = -10**18
            for q in [1,2,3,4]:
                for cw in [True, False]:
                    nb2 = _rotate_quadrant(nb, q, cw)
                    # opponent would benefit on their evaluation, but that's not directly the same move.
                    # Still, if opponent can win immediately for some rotation, it indicates fragility.
                    sc_opp = _evaluate(nb2, opp)
                    if sc_opp > best_opp:
                        best_opp = sc_opp

            # Combine: sc_me already incorporates win/loss for me; add extra penalty if opponent can have five.
            # approximate: if opponent can win after any rotation from this position, penalize.
            opp_can_win_any = False
            for q in [1,2,3,4]:
                for cw in [True, False]:
                    nb3 = _rotate_quadrant(nb, q, cw)
                    if _has_five_in_row(nb3, opp):
                        opp_can_win_any = True
                        break
                if opp_can_win_any:
                    break

            tactical_penalty = -500000 if opp_can_win_any else 0
            sc = sc_me + tactical_penalty

            # Tie-break: prefer moves that also block opponent immediate five on current board.
            if sc > best_score:
                best_score = sc
                best_action = (r,c,q_me)

        # Compose action: place(r,c,q) where q is quadrant to rotate
        r,c,q = best_action
        return f"place({r+1},{c+1},{q})"

    # If it's rotate phase, choose best rotation.
    elif phase == "rotate":
        best_q = 1
        best_cw = True
        best_score = -10**18
        # Candidates: all rotations 8 possibilities
        for q in [1,2,3,4]:
            for cw in [True, False]:
                nb = _rotate_quadrant(board, q, cw)
                sc = _evaluate(nb, me)
                # Prefer winning rotations, then defensive
                if sc > best_score:
                    best_score = sc
                    best_q, best_cw = q, cw
        return f"rotate({best_q},{'clockwise' if best_cw else 'counterclockwise'})"

    # Fallback: return a legal-looking default
    return "place(1,1,1)"
