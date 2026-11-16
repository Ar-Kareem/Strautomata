
# Pentago policy
# Implements: def policy(you, opponent) -> str

import math

N = 6

# Precompute all 5-cell winning segments on the 6x6 board.
_LINES = []

# Horizontal and vertical length-5 windows
for r in range(6):
    for c in range(2):
        _LINES.append([(r, c + i) for i in range(5)])
for c in range(6):
    for r in range(2):
        _LINES.append([(r + i, c) for i in range(5)])

# Diagonal down-right length-5 windows
for r in range(2):
    for c in range(2):
        _LINES.append([(r + i, c + i) for i in range(5)])

# Diagonal down-left length-5 windows
for r in range(2):
    for c in range(4, 6):
        _LINES.append([(r + i, c - i) for i in range(5)])


def _to_list(a):
    return [[int(a[r][c]) for c in range(6)] for r in range(6)]


def _has_win(b):
    for line in _LINES:
        ok = True
        for r, c in line:
            if b[r][c] == 0:
                ok = False
                break
        if ok:
            return True
    return False


def _copy_board(b):
    return [row[:] for row in b]


def _rotate_pair(me, opp, quad, direction):
    """Rotate both boards' selected 3x3 quadrant in-place."""
    r0 = 0 if quad < 2 else 3
    c0 = 0 if quad % 2 == 0 else 3

    old_me = [[me[r0 + r][c0 + c] for c in range(3)] for r in range(3)]
    old_op = [[opp[r0 + r][c0 + c] for c in range(3)] for r in range(3)]

    if direction == "R":
        for r in range(3):
            for c in range(3):
                me[r0 + r][c0 + c] = old_me[2 - c][r]
                opp[r0 + r][c0 + c] = old_op[2 - c][r]
    else:
        for r in range(3):
            for c in range(3):
                me[r0 + r][c0 + c] = old_me[c][2 - r]
                opp[r0 + r][c0 + c] = old_op[c][2 - r]


def _apply_move(me, opp, move):
    """Return new boards after current player places on me and rotates."""
    r, c, q, d = move
    nm = _copy_board(me)
    no = _copy_board(opp)
    nm[r][c] = 1
    _rotate_pair(nm, no, q, d)
    return nm, no


def _legal_moves(me, opp):
    moves = []
    for r in range(6):
        for c in range(6):
            if me[r][c] == 0 and opp[r][c] == 0:
                for q in range(4):
                    moves.append((r, c, q, "L"))
                    moves.append((r, c, q, "R"))
    return moves


def _line_score(my_count, op_count):
    if my_count and op_count:
        return 0

    if my_count:
        if my_count >= 5:
            return 10000000
        # Strongly value open fours and threes.
        vals = [0, 2, 12, 90, 2500, 10000000]
        return vals[my_count]

    if op_count:
        if op_count >= 5:
            return -10000000
        # Blocking opponent threats is slightly more important.
        vals = [0, 3, 16, 130, 3600, 10000000]
        return -vals[op_count]

    return 1


def _center_bonus(me, opp):
    # Pentago has no single center, but the central 2x2 and near-center cells are valuable.
    weights = [
        [1, 2, 3, 3, 2, 1],
        [2, 4, 5, 5, 4, 2],
        [3, 5, 7, 7, 5, 3],
        [3, 5, 7, 7, 5, 3],
        [2, 4, 5, 5, 4, 2],
        [1, 2, 3, 3, 2, 1],
    ]
    s = 0
    for r in range(6):
        for c in range(6):
            if me[r][c]:
                s += weights[r][c]
            elif opp[r][c]:
                s -= weights[r][c]
    return s


def _heuristic(me, opp):
    my_win = _has_win(me)
    op_win = _has_win(opp)

    if my_win and not op_win:
        return 100000000
    if op_win and not my_win:
        return -100000000
    if my_win and op_win:
        return 0

    score = _center_bonus(me, opp)

    for line in _LINES:
        mc = 0
        oc = 0
        for r, c in line:
            mc += me[r][c]
            oc += opp[r][c]
        score += _line_score(mc, oc)

    # Additional local pattern reward: marbles in same quadrant can become powerful after rotation.
    for qr in (0, 3):
        for qc in (0, 3):
            m = 0
            o = 0
            for r in range(qr, qr + 3):
                for c in range(qc, qc + 3):
                    m += me[r][c]
                    o += opp[r][c]
            if m and not o:
                score += m * m
            elif o and not m:
                score -= o * o

    return score


def _move_to_string(m):
    r, c, q, d = m
    return f"{r + 1},{c + 1},{q},{d}"


def policy(you, opponent) -> str:
    try:
        me = _to_list(you)
        opp = _to_list(opponent)

        moves = _legal_moves(me, opp)
        if not moves:
            # Should never happen according to the prompt, but keep a valid-looking fallback.
            return "1,1,0,L"

        fallback = moves[0]

        # 1. Immediate winning move.
        immediate_draws = []
        scored_first_pass = []

        for mv in moves:
            nm, no = _apply_move(me, opp, mv)
            mw = _has_win(nm)
            ow = _has_win(no)

            if mw and not ow:
                return _move_to_string(mv)

            if mw and ow:
                immediate_draws.append(mv)

            scored_first_pass.append((_heuristic(nm, no), mv, nm, no))

        # 2. Sort by static quality, then search opponent replies for the best candidates.
        scored_first_pass.sort(reverse=True, key=lambda x: x[0])

        # Time-conscious pruning. Early game has many equivalent rotations.
        empties = sum(
            1
            for r in range(6)
            for c in range(6)
            if me[r][c] == 0 and opp[r][c] == 0
        )
        if empties > 28:
            candidate_limit = 72
            reply_limit = 96
        elif empties > 18:
            candidate_limit = 120
            reply_limit = 160
        else:
            candidate_limit = len(scored_first_pass)
            reply_limit = 10000

        candidates = scored_first_pass[:candidate_limit]

        best_score = -10**18
        best_move = fallback

        for base_score, mv, nm, no in candidates:
            # If move already lets opponent have a win and we do not, avoid unless forced.
            if _has_win(no) and not _has_win(nm):
                move_score = -100000000
                if move_score > best_score:
                    best_score = move_score
                    best_move = mv
                continue

            # Opponent to move: from their perspective, their board is no and ours is nm.
            replies = _legal_moves(no, nm)

            # Static ordering of replies from opponent perspective.
            reply_scored = []
            for rmv in replies:
                r_opp, r_me = _apply_move(no, nm, rmv)
                val_for_opp = _heuristic(r_opp, r_me)
                reply_scored.append((val_for_opp, rmv, r_opp, r_me))

            reply_scored.sort(reverse=True, key=lambda x: x[0])
            reply_scored = reply_scored[:reply_limit]

            worst_for_us = 10**18

            for opp_static, rmv, after_opp, after_me in reply_scored:
                opp_win = _has_win(after_opp)
                my_win = _has_win(after_me)

                if opp_win and not my_win:
                    us_val = -100000000
                elif opp_win and my_win:
                    us_val = 0
                else:
                    # Convert heuristic back to our perspective.
                    us_val = _heuristic(after_me, after_opp)

                if us_val < worst_for_us:
                    worst_for_us = us_val
                    # Alpha-style cutoff: this candidate is already worse.
                    if worst_for_us < best_score:
                        break

            # Blend immediate positional value with minimax safety.
            move_score = worst_for_us + 0.05 * base_score

            if move_score > best_score:
                best_score = move_score
                best_move = mv

        # If everything looks losing, an immediate draw is better than many losses.
        if best_score < -50000000 and immediate_draws:
            return _move_to_string(immediate_draws[0])

        return _move_to_string(best_move)

    except Exception:
        # Absolute safety fallback: find the first empty cell and rotate quadrant 0 left.
        try:
            for r in range(6):
                for c in range(6):
                    if int(you[r][c]) == 0 and int(opponent[r][c]) == 0:
                        return f"{r + 1},{c + 1},0,L"
        except Exception:
            pass
        return "1,1,0,L"
