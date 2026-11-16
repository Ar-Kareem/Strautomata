
# pentago_policy.py
# A self-contained Pentago policy.
# Required API:
#   def policy(you, opponent) -> str

import math
import random

N = 6
QUADS = {
    0: (0, 0),
    1: (0, 3),
    2: (3, 0),
    3: (3, 3),
}

# All length-5 windows on a 6x6 board: horizontal, vertical, and diagonals.
LINES5 = []
for r in range(6):
    for c in range(2):
        LINES5.append([(r, c + i) for i in range(5)])
for c in range(6):
    for r in range(2):
        LINES5.append([(r + i, c) for i in range(5)])
for r in range(2):
    for c in range(2):
        LINES5.append([(r + i, c + i) for i in range(5)])
for r in range(2):
    for c in range(4, 6):
        LINES5.append([(r + i, c - i) for i in range(5)])

# Also useful: all full length 6 lines, because 5-in-a-row can be embedded,
# and longer patterns indicate strong strategic shape.
LINES6 = []
for r in range(6):
    LINES6.append([(r, c) for c in range(6)])
for c in range(6):
    LINES6.append([(r, c) for r in range(6)])
LINES6.append([(i, i) for i in range(6)])
LINES6.append([(i, 5 - i) for i in range(6)])

CENTER_WEIGHTS = [
    [2, 3, 4, 4, 3, 2],
    [3, 5, 7, 7, 5, 3],
    [4, 7, 9, 9, 7, 4],
    [4, 7, 9, 9, 7, 4],
    [3, 5, 7, 7, 5, 3],
    [2, 3, 4, 4, 3, 2],
]


def _to_board(you, opponent):
    b = [[0] * 6 for _ in range(6)]
    for r in range(6):
        yr = you[r]
        orow = opponent[r]
        for c in range(6):
            if int(yr[c]):
                b[r][c] = 1
            elif int(orow[c]):
                b[r][c] = -1
    return b


def _copy_board(b):
    return [row[:] for row in b]


def _rotate_in_place(b, q, d):
    r0, c0 = QUADS[q]
    sub = [[b[r0 + r][c0 + c] for c in range(3)] for r in range(3)]
    if d == "R":
        for r in range(3):
            for c in range(3):
                b[r0 + r][c0 + c] = sub[2 - c][r]
    else:
        for r in range(3):
            for c in range(3):
                b[r0 + r][c0 + c] = sub[c][2 - r]


def _apply_move(b, r, c, q, d, player):
    nb = _copy_board(b)
    nb[r][c] = player
    _rotate_in_place(nb, q, d)
    return nb


def _has_win(b, player):
    for line in LINES5:
        ok = True
        for r, c in line:
            if b[r][c] != player:
                ok = False
                break
        if ok:
            return True
    return False


def _legal_moves(b):
    moves = []
    for r in range(6):
        for c in range(6):
            if b[r][c] == 0:
                for q in range(4):
                    # Include both directions. Some rotations can be equivalent
                    # in symmetric quadrants, but enumerating all is safer.
                    moves.append((r, c, q, "L"))
                    moves.append((r, c, q, "R"))
    return moves


def _line_score(my_count, op_count, empty_count):
    if my_count and op_count:
        return 0
    if my_count == 5:
        return 10000000
    if op_count == 5:
        return -10000000

    if my_count:
        # Live patterns. Four is a forced tactical priority.
        if my_count == 4:
            return 120000 + 1000 * empty_count
        if my_count == 3:
            return 7000 + 120 * empty_count
        if my_count == 2:
            return 600 + 30 * empty_count
        if my_count == 1:
            return 35
    if op_count:
        if op_count == 4:
            return -150000 - 1000 * empty_count
        if op_count == 3:
            return -9000 - 150 * empty_count
        if op_count == 2:
            return -700 - 30 * empty_count
        if op_count == 1:
            return -40
    return 0


def _evaluate(b):
    my_win = _has_win(b, 1)
    op_win = _has_win(b, -1)
    if my_win and op_win:
        return 0
    if my_win:
        return 100000000
    if op_win:
        return -100000000

    score = 0

    # Length-5 tactical windows.
    for line in LINES5:
        myc = opc = emp = 0
        for r, c in line:
            v = b[r][c]
            if v == 1:
                myc += 1
            elif v == -1:
                opc += 1
            else:
                emp += 1
        score += _line_score(myc, opc, emp)

    # Length-6 shape bonus: two separate 5-windows often overlap here.
    for line in LINES6:
        myc = opc = 0
        for r, c in line:
            v = b[r][c]
            if v == 1:
                myc += 1
            elif v == -1:
                opc += 1
        if myc and not opc:
            score += [0, 20, 120, 900, 5000, 30000, 80000][myc]
        elif opc and not myc:
            score -= [0, 25, 150, 1100, 6500, 40000, 90000][opc]

    # Positional preference.
    for r in range(6):
        for c in range(6):
            if b[r][c] == 1:
                score += CENTER_WEIGHTS[r][c] * 8
            elif b[r][c] == -1:
                score -= CENTER_WEIGHTS[r][c] * 9

    return score


def _opponent_has_immediate_win(b):
    # It is now opponent's turn. Can opponent make a non-draw winning move?
    for r, c, q, d in _legal_moves(b):
        nb = _apply_move(b, r, c, q, d, -1)
        ow = _has_win(nb, -1)
        mw = _has_win(nb, 1)
        if ow and not mw:
            return True
    return False


def _best_opponent_reply_score(b, limit_all=True):
    # Returns the best evaluation from opponent perspective converted to our score.
    # Opponent chooses move minimizing our evaluation.
    worst_for_us = 10**18
    moves = _legal_moves(b)

    # Move ordering for speed: try tactically promising opponent moves first.
    scored = []
    for m in moves:
        r, c, q, d = m
        nb = _apply_move(b, r, c, q, d, -1)
        ev = _evaluate(nb)
        scored.append((ev, m, nb))
    scored.sort(key=lambda x: x[0])  # low evaluation is good for opponent

    # Usually small enough: at most 35*8 = 280 first ply, second ply can be costly.
    # Limit replies adaptively to preserve 1 second.
    max_replies = len(scored) if limit_all and len(scored) <= 96 else 40

    for ev, m, nb in scored[:max_replies]:
        if _has_win(nb, -1) and not _has_win(nb, 1):
            return -100000000
        if ev < worst_for_us:
            worst_for_us = ev
    return worst_for_us


def _move_to_str(m):
    r, c, q, d = m
    return f"{r + 1},{c + 1},{q},{d}"


def policy(you, opponent) -> str:
    b = _to_board(you, opponent)
    moves = _legal_moves(b)

    # Absolute safety fallback; policy is guaranteed to return legal if an empty exists.
    fallback = moves[0]

    # 1. Take any immediate non-draw win.
    draw_wins = []
    for m in moves:
        r, c, q, d = m
        nb = _apply_move(b, r, c, q, d, 1)
        myw = _has_win(nb, 1)
        opw = _has_win(nb, -1)
        if myw and not opw:
            return _move_to_str(m)
        if myw and opw:
            draw_wins.append(m)

    # 2. Identify opponent immediate winning threats from current position.
    opponent_winning_moves = []
    for om in moves:
        r, c, q, d = om
        nb = _apply_move(b, r, c, q, d, -1)
        if _has_win(nb, -1) and not _has_win(nb, 1):
            opponent_winning_moves.append(om)

    # 3. Score all candidate moves.
    best_m = None
    best_score = -10**18

    # Move ordering: evaluate promising moves first.
    prelim = []
    for m in moves:
        r, c, q, d = m
        nb = _apply_move(b, r, c, q, d, 1)
        prelim.append((_evaluate(nb), m, nb))
    prelim.sort(key=lambda x: x[0], reverse=True)

    # Search more broadly early/midgame, less when board is open.
    empties = len(moves) // 8
    if empties > 24:
        candidate_limit = 80
    elif empties > 14:
        candidate_limit = 120
    else:
        candidate_limit = len(prelim)

    for base_ev, m, nb in prelim[:candidate_limit]:
        myw = _has_win(nb, 1)
        opw = _has_win(nb, -1)

        # Avoid moves that immediately draw by giving both wins unless no better exists.
        if myw and opw:
            score = 2000000
        elif opw and not myw:
            score = -90000000
        else:
            score = base_ev

        # If opponent has immediate win after this, heavily penalize.
        opp_can_win = _opponent_has_immediate_win(nb)
        if opp_can_win:
            score -= 50000000
        else:
            score += 250000

        # A shallow minimax reply makes the policy much less trap-prone.
        # Skip expensive reply search for obviously bad moves.
        if score > -10000000:
            reply_score = _best_opponent_reply_score(nb, limit_all=(empties <= 16))
            score = min(score, reply_score + 20000)

        # Slight deterministic preference for central placement.
        r, c, q, d = m
        score += CENTER_WEIGHTS[r][c]

        if score > best_score:
            best_score = score
            best_m = m

    # 4. If all searched moves are losing, a draw by simultaneous win is acceptable.
    if best_m is None and draw_wins:
        best_m = draw_wins[0]

    if best_m is None:
        best_m = fallback

    return _move_to_str(best_m)
