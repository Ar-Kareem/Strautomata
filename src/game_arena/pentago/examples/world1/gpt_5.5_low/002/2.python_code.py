
import time

# Precompute all 5-cell winning windows on a 6x6 board.
_LINES = []
for r in range(6):
    for c in range(2):
        _LINES.append([(r, c + i) for i in range(5)])
for c in range(6):
    for r in range(2):
        _LINES.append([(r + i, c) for i in range(5)])
for r in range(2):
    for c in range(2):
        _LINES.append([(r + i, c + i) for i in range(5)])
for r in range(2):
    for c in range(4, 6):
        _LINES.append([(r + i, c - i) for i in range(5)])

# Quadrant top-left corners.
_QBASE = {
    0: (0, 0),
    1: (0, 3),
    2: (3, 0),
    3: (3, 3),
}

# Positional weights: mild preference for central and strategically flexible cells.
_POS_W = [
    [2, 3, 4, 4, 3, 2],
    [3, 5, 6, 6, 5, 3],
    [4, 6, 8, 8, 6, 4],
    [4, 6, 8, 8, 6, 4],
    [3, 5, 6, 6, 5, 3],
    [2, 3, 4, 4, 3, 2],
]

_SCORE = [0, 1, 12, 90, 1200, 1000000]


def _to_list_board(b):
    return [[1 if b[r][c] else 0 for c in range(6)] for r in range(6)]


def _has_win(b):
    for line in _LINES:
        ok = True
        for r, c in line:
            if not b[r][c]:
                ok = False
                break
        if ok:
            return True
    return False


def _rotate_quad(board, quad, direction):
    r0, c0 = _QBASE[quad]
    old = [[board[r0 + r][c0 + c] for c in range(3)] for r in range(3)]

    if direction == "R":
        for r in range(3):
            for c in range(3):
                board[r0 + r][c0 + c] = old[2 - c][r]
    else:
        for r in range(3):
            for c in range(3):
                board[r0 + r][c0 + c] = old[c][2 - r]


def _apply_move(me, opp, move):
    r, c, q, d = move

    nm = [row[:] for row in me]
    no = [row[:] for row in opp]

    nm[r][c] = 1

    _rotate_quad(nm, q, d)
    _rotate_quad(no, q, d)

    return nm, no


def _legal_moves(me, opp):
    moves = []
    for r in range(6):
        for c in range(6):
            if not me[r][c] and not opp[r][c]:
                for q in range(4):
                    moves.append((r, c, q, "L"))
                    moves.append((r, c, q, "R"))
    return moves


def _move_to_str(m):
    r, c, q, d = m
    return f"{r + 1},{c + 1},{q},{d}"


def _heuristic(me, opp):
    # Terminal states should normally be handled outside, but keeping this
    # makes the evaluator safer.
    mw = _has_win(me)
    ow = _has_win(opp)
    if mw and not ow:
        return 10**9
    if ow and not mw:
        return -10**9
    if mw and ow:
        return 0

    score = 0

    # Line potential.
    for line in _LINES:
        mc = 0
        oc = 0
        for r, c in line:
            if me[r][c]:
                mc += 1
            elif opp[r][c]:
                oc += 1

        if oc == 0:
            score += _SCORE[mc]
        elif mc == 0:
            score -= _SCORE[oc] * 1.12

    # Positional preference.
    for r in range(6):
        for c in range(6):
            if me[r][c]:
                score += _POS_W[r][c]
            elif opp[r][c]:
                score -= _POS_W[r][c]

    return score


def policy(you, opponent) -> str:
    start = time.time()
    TIME_LIMIT = 0.92

    me = _to_list_board(you)
    opp = _to_list_board(opponent)

    moves = _legal_moves(me, opp)

    # Absolute safety fallback.
    if not moves:
        return "1,1,0,L"
    fallback = _move_to_str(moves[0])

    # 1. Immediate winning move.
    draw_moves = []
    scored = []

    for m in moves:
        nm, no = _apply_move(me, opp, m)
        mw = _has_win(nm)
        ow = _has_win(no)

        if mw and not ow:
            return _move_to_str(m)

        if mw and ow:
            draw_moves.append(m)

        scored.append((_heuristic(nm, no), m, nm, no))

    # 2. Sort candidate moves by static evaluation.
    scored.sort(reverse=True, key=lambda x: x[0])

    empties = 0
    for r in range(6):
        for c in range(6):
            if not me[r][c] and not opp[r][c]:
                empties += 1

    # Analyze more moves in the endgame, fewer in the opening.
    if empties <= 10:
        candidate_count = len(scored)
    elif empties <= 20:
        candidate_count = min(len(scored), 80)
    else:
        candidate_count = min(len(scored), 48)

    best_move = scored[0][1]
    best_value = -10**18

    # 3. One-ply opponent reply search over best candidates.
    for idx in range(candidate_count):
        if time.time() - start > TIME_LIMIT:
            break

        base_score, m, nm, no = scored[idx]

        mw = _has_win(nm)
        ow = _has_win(no)

        if mw and ow:
            value = 0
            if value > best_value:
                best_value = value
                best_move = m
            continue

        # Opponent to move: from their perspective, their board is no.
        opp_replies = _legal_moves(no, nm)
        worst = 10**18

        for om in opp_replies:
            if time.time() - start > TIME_LIMIT:
                break

            # Apply opponent move.
            ono, onm = _apply_move(no, nm, om)

            opp_win = _has_win(ono)
            our_win = _has_win(onm)

            if opp_win and not our_win:
                reply_value = -10**9
            elif opp_win and our_win:
                reply_value = 0
            elif our_win and not opp_win:
                reply_value = 10**9
            else:
                reply_value = _heuristic(onm, ono)

            if reply_value < worst:
                worst = reply_value

            # Early cutoff: this candidate allows immediate opponent win.
            if worst <= -10**9:
                break

        # Blend static and reply value slightly. The reply value dominates.
        if worst == 10**18:
            value = base_score
        else:
            value = worst + 0.01 * base_score

        if value > best_value:
            best_value = value
            best_move = m

    # If all serious candidates are losing and we have a draw move, prefer draw.
    if best_value < -10**8 and draw_moves:
        return _move_to_str(draw_moves[0])

    # Final legality safety check.
    r, c, q, d = best_move
    if 0 <= r < 6 and 0 <= c < 6 and q in (0, 1, 2, 3) and d in ("L", "R"):
        if not me[r][c] and not opp[r][c]:
            return _move_to_str(best_move)

    return fallback
