
import random
from collections import deque

BOARD_N = 19

def _neighbors(r, c):
    if r > 1: yield (r-1, c)
    if r < BOARD_N: yield (r+1, c)
    if c > 1: yield (r, c-1)
    if c < BOARD_N: yield (r, c+1)

def _in_bounds(r, c):
    return 1 <= r <= BOARD_N and 1 <= c <= BOARD_N

def _get_board(me, opponent):
    # 0 empty, 1 me, 2 opp
    b = [[0]* (BOARD_N+1) for _ in range(BOARD_N+1)]
    for r,c in me:
        if _in_bounds(r,c): b[r][c] = 1
    for r,c in opponent:
        if _in_bounds(r,c): b[r][c] = 2
    return b

def _group_and_liberties(board, sr, sc, color):
    # BFS group
    visited = set()
    q = deque([(sr, sc)])
    visited.add((sr, sc))
    libs = set()
    while q:
        r, c = q.popleft()
        for nr, nc in _neighbors(r,c):
            if board[nr][nc] == 0:
                libs.add((nr, nc))
            elif board[nr][nc] == color and (nr, nc) not in visited:
                visited.add((nr, nc))
                q.append((nr, nc))
    return visited, libs

def _would_capture(board, r, c, color):
    opp = 3 - color
    captured = []
    for nr, nc in _neighbors(r,c):
        if board[nr][nc] == opp:
            grp, libs = _group_and_liberties(board, nr, nc, opp)
            if (r, c) in grp or True:
                # After placing at (r,c), that point becomes occupied, reducing liberties by 1
                # Capture occurs if the group had exactly this liberty.
                # But (r,c) is currently empty so it is indeed one of group's liberties if legal.
                if (r, c) in libs and len(libs) == 1:
                    captured.append(grp)
    return captured

def _simulate_move_legal(board, r, c, color):
    # Basic legality: point must be empty; after move, own group must have liberties or capture occurs.
    if board[r][c] != 0:
        return False
    opp = 3 - color

    # Place temporarily
    board[r][c] = color

    # Remove captured opponent groups
    captured_any = False
    to_remove = []
    for nr, nc in _neighbors(r,c):
        if board[nr][nc] == opp:
            grp, libs = _group_and_liberties(board, nr, nc, opp)
            if len(libs) == 0:
                to_remove.append(grp)
    for grp in to_remove:
        captured_any = True
        for gr,gc in grp:
            board[gr][gc] = 0

    # Check liberties of own group
    grp, libs = _group_and_liberties(board, r, c, color)
    legal = (len(libs) > 0)
    # Revert: we can't easily revert multiple removals without copy.
    # Caller uses a copied board for legality checks; keep this function simple.
    # We'll revert by reconstructing outside.
    return legal

def _copy_board(board):
    return [row[:] for row in board]

def _legal_moves(me, opponent):
    board = _get_board(me, opponent)
    color = 1  # our stones
    legal = []
    # Generate candidate empties near stones to save time
    stones = set(me) | set(opponent)
    candidates = set()
    if stones:
        for r,c in stones:
            for nr,nc in _neighbors(r,c):
                if board[nr][nc] == 0:
                    candidates.add((nr,nc))
    else:
        candidates = {(9,9)}  # empty board: center bias

    # Also consider a few center points if not in candidates
    for r in range(8,12):
        for c in range(8,12):
            if _in_bounds(r,c) and board[r][c] == 0:
                candidates.add((r,c))

    # Evaluate legality
    for r,c in candidates:
        b2 = _copy_board(board)
        if _simulate_move_legal(b2, r, c, color):
            legal.append((r,c))
    # If none found, broaden to all empties (still fine: 361 max)
    if not legal:
        for r in range(1, BOARD_N+1):
            for c in range(1, BOARD_N+1):
                if board[r][c] == 0:
                    b2 = _copy_board(board)
                    if _simulate_move_legal(b2, r, c, color):
                        legal.append((r,c))
    return legal

def _count_liberties_of_weak_group(board, color):
    # Find groups and return list of (min_libs, any_cell)
    seen = set()
    out = []
    for r in range(1, BOARD_N+1):
        for c in range(1, BOARD_N+1):
            if board[r][c] == color and (r,c) not in seen:
                grp, libs = _group_and_liberties(board, r, c, color)
                for cell in grp:
                    seen.add(cell)
                out.append((len(libs), next(iter(grp))))
    return out

def _choose_move(me, opponent):
    board = _get_board(me, opponent)
    opp = 2
    color = 1

    all_stones = set(me) | set(opponent)
    # Candidate moves: adjacent to any stone, plus center-ish
    candidates = set()
    for r,c in all_stones:
        for nr,nc in _neighbors(r,c):
            if board[nr][nc] == 0:
                candidates.add((nr,nc))
    for r in range(1, BOARD_N+1):
        pass
    for r in range(8,12):
        for c in range(8,12):
            if board[r][c] == 0:
                candidates.add((r,c))
    if not candidates:
        candidates = {(9,9)}

    def score_move(r, c):
        # Higher is better
        # If move illegal, return very low.
        b2 = _copy_board(board)
        if not _simulate_move_legal(b2, r, c, color):
            return -10**9

        # Prefer capturing
        captured = 0
        for nr, nc in _neighbors(r,c):
            if board[nr][nc] == opp:
                grp, libs = _group_and_liberties(board, nr, nc, opp)
                if (r,c) in libs and len(libs) == 1:
                    captured += len(grp)
        s = captured * 1000

        # If we don't capture, ensure we don't give opponent immediate capture
        # (simulate opponent capturing at each neighbor empty after our move)
        b_after = _copy_board(board)
        b_after[r][c] = color
        # remove captured groups for opponent correctly
        for nr, nc in _neighbors(r,c):
            if b_after[nr][nc] == opp:
                grp, libs = _group_and_liberties(b_after, nr, nc, opp)
                if len(libs) == 0:
                    for gr,gc in grp:
                        b_after[gr][gc] = 0

        # Now check opponent immediate captures adjacent to our move position (local threat)
        threat = 0
        for tr, tc in _neighbors(r,c):
            if _in_bounds(tr,tc) and b_after[tr][tc] == 0:
                # Can opponent play there and capture?
                o_color = opp
                # legality for opponent
                b3 = _copy_board(b_after)
                if _simulate_move_legal(b3, tr, tc, o_color):
                    # count captures
                    cap = 0
                    for anr, anc in _neighbors(tr,tc):
                        if b_after[anr][anc] == color:
                            grp, libs = _group_and_liberties(b_after, anr, anc, color)
                            if (tr,tc) in libs and len(libs) == 1:
                                cap += len(grp)
                    threat = max(threat, cap)
        s -= threat * 120

        # Prefer moves that connect groups / improve liberties
        # Evaluate our resulting group liberties
        grp, libs = _group_and_liberties(b_after, r, c, color)
        s += len(libs) * 30

        # Distance to center heuristic
        center = 10
        s += (20 - (abs(r-center)+abs(c-center))) * 1.5

        # Slight bias to avoid edges late? mild:
        s += (min(r-1, BOARD_N-r, c-1, BOARD_N-c)) * 0.2

        return s

    best = None
    best_s = -10**18
    # If candidates might include many illegal, still fine.
    for r,c in candidates:
        s = score_move(r,c)
        if s > best_s:
            best_s = s
            best = (r,c)

    # Ensure legality; if not, fall back to legal move list
    if best is not None:
        b0 = _copy_board(board)
        if _simulate_move_legal(b0, best[0], best[1], color):
            return best

    legals = _legal_moves(me, opponent)
    if legals:
        # choose best among legals
        best = max(legals, key=lambda mv: score_move(mv[0], mv[1]))
        return best

    return (0,0)

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    return _choose_move(me, opponent)
