
import random
from typing import List, Tuple

# ---------------- Pentago Utilities ----------------

N = 6
QSIZE = 3

def _rotate_quadrant(board_6x6, quad: int, dir_ch: str):
    """Rotate 3x3 quadrant of board_6x6 in place, affects that array only.
    dir_ch: 'L' anticlockwise or 'R' clockwise."""
    r0 = 0 if quad in (0, 1) else 3
    c0 = 0 if quad in (0, 2) else 3

    # Extract 3x3
    mat = [[board_6x6[r0 + i][c0 + j] for j in range(QSIZE)] for i in range(QSIZE)]

    if dir_ch == 'R':
        # clockwise: new[i][j] = old[2-j][i]
        new = [[mat[QSIZE - 1 - j][i] for j in range(QSIZE)] for i in range(QSIZE)]
    else:
        # anticlockwise: new[i][j] = old[j][2-i]
        new = [[mat[j][QSIZE - 1 - i] for j in range(QSIZE)] for i in range(QSIZE)]

    for i in range(QSIZE):
        for j in range(QSIZE):
            board_6x6[r0 + i][c0 + j] = new[i][j]

def _apply_move(you, opp, row1, col1, quad, dir_ch):
    """Return (new_you, new_opp) as deep-copied 2D lists."""
    r = row1 - 1
    c = col1 - 1
    new_you = [list(rw) for rw in you]
    new_opp = [list(rw) for rw in opp]
    new_you[r][c] = 1
    _rotate_quadrant(new_you, quad, dir_ch)
    _rotate_quadrant(new_opp, quad, dir_ch)  # opponent marbles in that quadrant also rotate
    return new_you, new_opp

def _has_five_in_row(board):
    """Check if board has 5+ in a row (straight lines)."""
    # horizontal
    for r in range(N):
        run = 0
        for c in range(N):
            if board[r][c]:
                run += 1
                if run >= 5:
                    return True
            else:
                run = 0
    # vertical
    for c in range(N):
        run = 0
        for r in range(N):
            if board[r][c]:
                run += 1
                if run >= 5:
                    return True
            else:
                run = 0
    # diag down-right
    for sr in range(N):
        r, c = sr, 0
        run = 0
        while r < N and c < N:
            if board[r][c]:
                run += 1
                if run >= 5:
                    return True
            else:
                run = 0
            r += 1
            c += 1
    for sc in range(1, N):
        r, c = 0, sc
        run = 0
        while r < N and c < N:
            if board[r][c]:
                run += 1
                if run >= 5:
                    return True
            else:
                run = 0
            r += 1
            c += 1
    # diag down-left
    for sr in range(N):
        r, c = sr, N - 1
        run = 0
        while r < N and c >= 0:
            if board[r][c]:
                run += 1
                if run >= 5:
                    return True
            else:
                run = 0
            r += 1
            c -= 1
    for sc in range(N - 2, -1, -1):
        r, c = 0, sc
        run = 0
        while r < N and c >= 0:
            if board[r][c]:
                run += 1
                if run >= 5:
                    return True
            else:
                run = 0
            r += 1
            c -= 1
    return False

def _lines_for_eval():
    """Precompute all straight lines segments of length 5+? For heuristic, use exact length-5 windows."""
    windows = []
    # each window is list of (r,c) length 5
    # horizontal
    for r in range(N):
        for c in range(N - 4):
            windows.append([(r, c+i) for i in range(5)])
    # vertical
    for c in range(N):
        for r in range(N - 4):
            windows.append([(r+i, c) for i in range(5)])
    # diag down-right
    for r in range(N - 4):
        for c in range(N - 4):
            windows.append([(r+i, c+i) for i in range(5)])
    # diag down-left
    for r in range(N - 4):
        for c in range(4, N):
            windows.append([(r+i, c-i) for i in range(5)])
    return windows

_WINDOWS5 = _lines_for_eval()

def _heuristic_score(you, opp):
    """Higher is better for you."""
    # If someone already has five, score heavily (handled elsewhere, but keep consistent)
    if _has_five_in_row(you):
        return 10_000
    if _has_five_in_row(opp):
        return -10_000

    score = 0
    # evaluate windows of length 5
    for w in _WINDOWS5:
        y = 0
        o = 0
        for r, c in w:
            if you[r][c]:
                y += 1
            elif opp[r][c]:
                o += 1
        if o and y:
            continue  # blocked window
        if y and not o:
            # reward near-complete
            if y == 4:
                score += 120
            elif y == 3:
                score += 25
            elif y == 2:
                score += 6
            elif y == 1:
                score += 1
        elif o and not y:
            # punish opponent near-complete
            if o == 4:
                score -= 160
            elif o == 3:
                score -= 30
            elif o == 2:
                score -= 7
            elif o == 1:
                score -= 2

    # center preference (after considering rotation, still helps)
    center = {(2,2),(2,3),(3,2),(3,3)}  # 0-indexed around the middle
    for (r,c) in center:
        if you[r][c]:
            score += 10
        if opp[r][c]:
            score -= 10

    # slight mobility/compactness not computed; keep cheap
    return score

def _legal_moves(you, opp):
    empties = []
    for r in range(N):
        for c in range(N):
            if you[r][c] == 0 and opp[r][c] == 0:
                empties.append((r+1, c+1))
    moves = []
    for (row1, col1) in empties:
        for quad in range(4):
            moves.append((row1, col1, quad, 'L'))
            moves.append((row1, col1, quad, 'R'))
    return moves

def _opponent_can_win_next(you_after, opp_after):
    """Check whether opponent has any immediate winning move from this state.
    Opponent plays like "you" next: places one marble then rotates one quadrant.
    Return True if any opponent move yields opponent five-in-row (you-after irrelevant except for legality)."""
    # Build empties from combined occupancy
    # We treat opponent as "to move" with their board = opp_after.
    for row1 in range(1, N+1):
        for col1 in range(1, N+1):
            r = row1-1
            c = col1-1
            if you_after[r][c] == 0 and opp_after[r][c] == 0:
                for quad in range(4):
                    for dir_ch in ('L', 'R'):
                        # apply: opponent places at (row1,col1), rotate quadrant affecting both
                        new_opp = [list(rw) for rw in opp_after]
                        new_you = [list(rw) for rw in you_after]
                        new_opp[r][c] = 1
                        _rotate_quadrant(new_opp, quad, dir_ch)
                        _rotate_quadrant(new_you, quad, dir_ch)
                        if _has_five_in_row(new_opp):
                            return True
    return False

# ---------------- Main Policy ----------------

def policy(you, opponent) -> str:
    # Deterministic randomness for tie-breaking
    rnd = random.Random(1337)

    # Convert to lists (in case input is numpy)
    you = [list(map(int, row)) for row in you]
    opponent = [list(map(int, row)) for row in opponent]

    moves = _legal_moves(you, opponent)

    best_win = None
    best_block = None
    best_score = -10**18
    best_move = None

    # 1) Immediate win and 2) blocking by removing all opponent immediate wins
    for (row1, col1, quad, dir_ch) in moves:
        new_you, new_opp = _apply_move(you, opponent, row1, col1, quad, dir_ch)

        you_win = _has_five_in_row(new_you)
        opp_win = _has_five_in_row(new_opp)

        if you_win:
            # If both win, draw but still preferable over non-win.
            # As per statement: if both have 5 after your move, result is draw.
            return f"{row1},{col1},{quad},{dir_ch}"

    # No immediate win: search for best block candidates
    for (row1, col1, quad, dir_ch) in moves:
        new_you, new_opp = _apply_move(you, opponent, row1, col1, quad, dir_ch)

        # Avoid letting opponent win immediately if possible
        if _has_five_in_row(new_opp):
            continue

        # If opponent cannot win on their next move, it's a strong block.
        if not _opponent_can_win_next(new_you, new_opp):
            # Score these blocks too
            sc = _heuristic_score(new_you, new_opp)
            # tie-break with small randomness
            sc += rnd.randint(-3, 3)
            if sc > best_score:
                best_score = sc
                best_move = (row1, col1, quad, dir_ch)

    if best_move is not None:
        return f"{best_move[0]},{best_move[1]},{best_move[2]},{best_move[3]}"

    # Otherwise: heuristic best move
    for (row1, col1, quad, dir_ch) in moves:
        new_you, new_opp = _apply_move(you, opponent, row1, col1, quad, dir_ch)

        # Slight penalty if opponent already has five (usually avoid)
        sc = _heuristic_score(new_you, new_opp)
        sc += rnd.randint(-3, 3)

        if sc > best_score:
            best_score = sc
            best_move = (row1, col1, quad, dir_ch)

    # Must return legal move string; best_move should exist.
    if best_move is None:
        # Fallback: pick first legal move
        row1, col1, quad, dir_ch = moves[0]
        return f"{row1},{col1},{quad},{dir_ch}"
    return f"{best_move[0]},{best_move[1]},{best_move[2]},{best_move[3]}"
