
import random
from itertools import product

N = 6

def _board_from_planes(you, opponent):
    # 0 empty, 1 us, 2 opp
    b = [[0]*N for _ in range(N)]
    for r in range(N):
        for c in range(N):
            if you[r][c]:
                b[r][c] = 1
            elif opponent[r][c]:
                b[r][c] = 2
    return b

def _clone_board(b):
    return [row[:] for row in b]

def _apply_rotation(board, quad, dir):
    # Rotate 3x3 in place anticlockwise if L else clockwise.
    # Quadrant mapping (0..3):
    # 0: rows0..2 cols0..2
    # 1: rows0..2 cols3..5
    # 2: rows3..5 cols0..2
    # 3: rows3..5 cols3..5
    rq = 0 if quad < 2 else 3
    cq = 0 if (quad % 2) == 0 else 3

    sub = [[board[rq+i][cq+j] for j in range(3)] for i in range(3)]
    if dir == 'L':  # 90 anticlockwise
        # new[i][j] = old[j][2-i]
        new = [[sub[j][2-i] for j in range(3)] for i in range(3)]
    else:  # 'R' clockwise
        # new[i][j] = old[2-j][i]
        new = [[sub[2-j][i] for j in range(3)] for i in range(3)]
    for i in range(3):
        for j in range(3):
            board[rq+i][cq+j] = new[i][j]

def _place_and_rotate(board, r, c, quad, dir):
    nb = _clone_board(board)
    nb[r][c] = 1
    _apply_rotation(nb, quad, dir)
    return nb

def _has_five(board, player):
    # Check for any line length >=5 in 6x6 board: horizontal, vertical, diag both.
    # Since win is 5 or more, but board is 6, just check all segments of length 5.
    need = 5
    # Horizontal
    for r in range(N):
        for c in range(N-need+1):
            ok = True
            for k in range(need):
                if board[r][c+k] != player:
                    ok = False
                    break
            if ok:
                return True
    # Vertical
    for c in range(N):
        for r in range(N-need+1):
            ok = True
            for k in range(need):
                if board[r+k][c] != player:
                    ok = False
                    break
            if ok:
                return True
    # Diagonal down-right
    for r in range(N-need+1):
        for c in range(N-need+1):
            ok = True
            for k in range(need):
                if board[r+k][c+k] != player:
                    ok = False
                    break
            if ok:
                return True
    # Diagonal down-left
    for r in range(N-need+1):
        for c in range(need-1, N):
            ok = True
            for k in range(need):
                if board[r+k][c-k] != player:
                    ok = False
                    break
            if ok:
                return True
    return False

def _segments_of_len5():
    segs = []
    need = 5
    # Generate all segments length 5; 6x6 => 16 horizontals + 16 verticals + 16 diagDR + 16 diagDL = 64
    for r in range(N):
        for c in range(N-need+1):
            segs.append([(r, c+k) for k in range(need)])
    for c in range(N):
        for r in range(N-need+1):
            segs.append([(r+k, c) for k in range(need)])
    for r in range(N-need+1):
        for c in range(N-need+1):
            segs.append([(r+k, c+k) for k in range(need)])
    for r in range(N-need+1):
        for c in range(need-1, N):
            segs.append([(r+k, c-k) for k in range(need)])
    return segs

SEGS5 = _segments_of_len5()

def _score_board(board):
    # Heuristic: count our/opp "open" segments and prioritize our segments with many marbles.
    # Also give some weight to near-complete lines (4 with no opponent in segment).
    score = 0

    def seg_score(seg, player):
        # returns integer based on counts in segment: if opponent present => 0
        cnt = 0
        other = 0
        for r,c in seg:
            v = board[r][c]
            if v == player:
                cnt += 1
            elif v != 0:
                other += 1
        if other > 0:
            return 0
        # Only our marbles and empties
        # cnt==5 win already handled outside, but still give huge weight.
        if cnt == 4:
            return 1000
        if cnt == 3:
            return 150
        if cnt == 2:
            return 25
        if cnt == 1:
            return 5
        return 0

    # Our potential
    for seg in SEGS5:
        score += seg_score(seg, 1)
    # Opponent threat: subtract potential
    for seg in SEGS5:
        score -= int(seg_score(seg, 2) * 1.05)

    # Small extra: center-ish preference
    center = {(2,2),(2,3),(3,2),(3,3)}
    for r in range(N):
        for c in range(N):
            if board[r][c] == 1:
                score += 2 if (r,c) in center else 0
            elif board[r][c] == 2:
                score -= 2 if (r,c) in center else 0

    return score

def policy(you, opponent) -> str:
    board0 = _board_from_planes(you, opponent)

    # Enumerate empty cells
    empties = [(r,c) for r in range(N) for c in range(N) if board0[r][c] == 0]

    # Precompute all candidate moves (placement + rotation)
    dirs = ['L', 'R']
    candidates = []
    for r,c in empties:
        # Choose one of four quadrants to rotate regardless of placement location (always legal as long as cell empty)
        for quad in range(4):
            for d in dirs:
                candidates.append((r,c,quad,d))

    # Immediate win check and immediate block check
    winning_moves = []
    best_move = None
    best_score = -10**18
    # For blocking, we need to know if after our move, opponent has a winning move next.
    # We'll test each candidate by scanning opponent winning responses (expensive but manageable).
    # Typical branching: <= 36 empties * 4 * 2 = 288 candidates; opponent response checks another <= 288.
    # Worst-case ~ 83k board evals, each eval includes a rotation on small matrix => fine in 1 sec in Python.

    # Cache for our board evaluations maybe not needed.

    for (r,c,quad,d) in candidates:
        b_after = _place_and_rotate(board0, r, c, quad, d)

        if _has_five(b_after, 1):
            winning_moves.append((r,c,quad,d))
            continue

        # Check opponent immediate win after our move
        opp_wins = False
        # If board is almost full, fewer empties.
        empties_after = [(rr,cc) for rr in range(N) for cc in range(N) if b_after[rr][cc] == 0]
        for (orow,ocol) in empties_after:
            # Opponent places a marble on (orow,ocol) then rotates some quad with either dir.
            for oquad in range(4):
                for od in dirs:
                    b_opp = _clone_board(b_after)
                    b_opp[orow][ocol] = 2
                    _apply_rotation(b_opp, oquad, od)
                    if _has_five(b_opp, 2):
                        opp_wins = True
                        break
                if opp_wins:
                    break
            if opp_wins:
                break

        if opp_wins:
            # Strongly avoid moves that give opponent a win immediately,
            # but still allow if no other move exists (handled later).
            continue

        sc = _score_board(b_after)
        # Slight preference to reduce opponent's potential more (already in scoring, but reinforce)
        # and prefer moves that increase our potential linearly.
        sc += random.randint(0, 3)

        if sc > best_score:
            best_score = sc
            best_move = (r,c,quad,d)

    # If we have winning moves, take one (prefer higher heuristic too)
    if winning_moves:
        if len(winning_moves) == 1:
            r,c,quad,d = winning_moves[0]
            return f"{r+1},{c+1},{quad},{d}"
        # choose best among winning ones by tie-break score (still legal)
        best = None
        best_sc = -10**18
        for (r,c,quad,d) in winning_moves:
            b_after = _place_and_rotate(board0, r, c, quad, d)
            sc = _score_board(b_after)
            # Add small randomness
            sc += random.randint(0, 5)
            if sc > best_sc:
                best_sc = sc
                best = (r,c,quad,d)
        r,c,quad,d = best
        return f"{r+1},{c+1},{quad},{d}"

    # Otherwise, take best safe move if found
    if best_move is not None:
        r,c,quad,d = best_move
        return f"{r+1},{c+1},{quad},{d}"

    # Fallback: if all moves allow an immediate opponent win, pick the one that
    # minimizes opponent's immediate winning potential (or maximizes our score).
    fallback_best = None
    fallback_sc = -10**18
    for (r,c,quad,d) in candidates:
        b_after = _place_and_rotate(board0, r, c, quad, d)
        # Count how many opponent immediate winning moves exist (approx)
        cnt_opp_win = 0
        empties_after = [(rr,cc) for rr in range(N) for cc in range(N) if b_after[rr][cc] == 0]
        for (orow,ocol) in empties_after:
            for oquad in range(4):
                for od in dirs:
                    b_opp = _clone_board(b_after)
                    b_opp[orow][ocol] = 2
                    _apply_rotation(b_opp, oquad, od)
                    if _has_five(b_opp, 2):
                        cnt_opp_win += 1
        sc = _score_board(b_after) - 2000 * cnt_opp_win + random.randint(0, 7)
        if sc > fallback_sc:
            fallback_sc = sc
            fallback_best = (r,c,quad,d)

    r,c,quad,d = fallback_best
    return f"{r+1},{c+1},{quad},{d}"
