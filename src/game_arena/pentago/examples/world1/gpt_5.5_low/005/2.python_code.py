
# Pentago policy
# Required API:
#   def policy(you, opponent) -> str

import math

N = 6

# All contiguous 5-cell winning windows on a 6x6 board.
_WIN_LINES = []
for r in range(N):
    for c in range(N):
        for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
            rr = r + 4 * dr
            cc = c + 4 * dc
            if 0 <= rr < N and 0 <= cc < N:
                _WIN_LINES.append(tuple((r + i * dr, c + i * dc) for i in range(5)))

# Positional preference. Pentago rotations make many squares useful, but central-ish
# and quadrant centers/corners are generally valuable.
_POS_WEIGHT = [
    [3, 4, 4, 4, 4, 3],
    [4, 6, 5, 5, 6, 4],
    [4, 5, 7, 7, 5, 4],
    [4, 5, 7, 7, 5, 4],
    [4, 6, 5, 5, 6, 4],
    [3, 4, 4, 4, 4, 3],
]

# Score for a non-blocked 5-window containing k stones.
_COUNT_SCORE = [0, 2, 12, 80, 1200, 1000000]


def _to_board(a):
    """Convert array-like 6x6 to plain list of lists of ints."""
    return [[1 if a[r][c] else 0 for c in range(N)] for r in range(N)]


def _has_win(b):
    """True if board b has at least one contiguous 5-in-a-row."""
    for line in _WIN_LINES:
        ok = True
        for r, c in line:
            if not b[r][c]:
                ok = False
                break
        if ok:
            return True
    return False


def _full(y, o):
    for r in range(N):
        for c in range(N):
            if not y[r][c] and not o[r][c]:
                return False
    return True


def _copy_boards(y, o):
    return [row[:] for row in y], [row[:] for row in o]


def _rotate_quad(y, o, q, d):
    """Rotate quadrant q in-place on both boards."""
    r0 = 0 if q < 2 else 3
    c0 = 0 if q % 2 == 0 else 3

    old_y = [[y[r0 + i][c0 + j] for j in range(3)] for i in range(3)]
    old_o = [[o[r0 + i][c0 + j] for j in range(3)] for i in range(3)]

    if d == "R":
        for i in range(3):
            for j in range(3):
                y[r0 + i][c0 + j] = old_y[2 - j][i]
                o[r0 + i][c0 + j] = old_o[2 - j][i]
    else:
        for i in range(3):
            for j in range(3):
                y[r0 + i][c0 + j] = old_y[j][2 - i]
                o[r0 + i][c0 + j] = old_o[j][2 - i]


def _apply_move(y, o, r, c, q, d, placer_is_y=True):
    """
    Return new boards after placing for y if placer_is_y else for o,
    then rotating quadrant.
    r,c are zero-indexed.
    """
    ny, no = _copy_boards(y, o)
    if placer_is_y:
        ny[r][c] = 1
    else:
        no[r][c] = 1
    _rotate_quad(ny, no, q, d)
    return ny, no


def _legal_moves(y, o):
    moves = []
    for r in range(N):
        for c in range(N):
            if not y[r][c] and not o[r][c]:
                for q in range(4):
                    moves.append((r, c, q, "L"))
                    moves.append((r, c, q, "R"))
    return moves


def _static_eval(y, o):
    """
    Heuristic from current policy player's perspective.
    Positive is good for y, negative is good for o.
    """
    yw = _has_win(y)
    ow = _has_win(o)
    if yw and not ow:
        return 100000000
    if ow and not yw:
        return -100000000
    if yw and ow:
        return 0

    score = 0

    # Line-window scoring.
    for line in _WIN_LINES:
        yc = 0
        oc = 0
        for r, c in line:
            yc += y[r][c]
            oc += o[r][c]

        if yc and oc:
            continue
        if yc:
            score += _COUNT_SCORE[yc]
        elif oc:
            score -= _COUNT_SCORE[oc]

    # Positional scoring.
    for r in range(N):
        for c in range(N):
            if y[r][c]:
                score += _POS_WEIGHT[r][c]
            elif o[r][c]:
                score -= _POS_WEIGHT[r][c]

    return score


def _format_move(m):
    r, c, q, d = m
    return f"{r + 1},{c + 1},{q},{d}"


def policy(you, opponent) -> str:
    try:
        y = _to_board(you)
        o = _to_board(opponent)
        moves = _legal_moves(y, o)

        # Guaranteed by prompt, but keep a safety fallback.
        if not moves:
            return "1,1,0,L"

        best_move = moves[0]
        best_score = -10**18

        # First pass: immediate decisive wins.
        immediate_draw = None
        for m in moves:
            r, c, q, d = m
            ny, no = _apply_move(y, o, r, c, q, d, True)
            yw = _has_win(ny)
            ow = _has_win(no)
            if yw and not ow:
                return _format_move(m)
            if yw and ow and immediate_draw is None:
                immediate_draw = m

        # One-ply minimax: for each of our moves, assume opponent makes the
        # strongest immediate reply.
        for m in moves:
            r, c, q, d = m
            ny, no = _apply_move(y, o, r, c, q, d, True)

            yw = _has_win(ny)
            ow = _has_win(no)

            if ow and not yw:
                # Our move immediately gives opponent a win.
                candidate_score = -1000000000
            elif yw and ow:
                # Draw by simultaneous five-in-a-row.
                candidate_score = 0
            elif _full(ny, no):
                candidate_score = 0
            else:
                opp_moves = _legal_moves(ny, no)
                worst_reply_score = 10**18

                for om in opp_moves:
                    rr, cc, qq, dd = om
                    # Opponent places on no-board.
                    ry, ro = _apply_move(ny, no, rr, cc, qq, dd, False)

                    ryw = _has_win(ry)
                    row = _has_win(ro)

                    if row and not ryw:
                        reply_score = -100000000
                    elif ryw and not row:
                        reply_score = 100000000
                    elif ryw and row:
                        reply_score = 0
                    elif _full(ry, ro):
                        reply_score = 0
                    else:
                        reply_score = _static_eval(ry, ro)

                    if reply_score < worst_reply_score:
                        worst_reply_score = reply_score
                        # Alpha-style early exit if this move is already awful.
                        if worst_reply_score < best_score - 5000:
                            break

                candidate_score = worst_reply_score

            # Small deterministic tie-breaker favoring stronger static position.
            candidate_score += 0.001 * _static_eval(ny, no)

            if candidate_score > best_score:
                best_score = candidate_score
                best_move = m

        # If everything looks losing but we can force an immediate draw, prefer it.
        if best_score < -50000000 and immediate_draw is not None:
            return _format_move(immediate_draw)

        return _format_move(best_move)

    except Exception:
        # Absolute safety: find the first legal-looking empty square and return
        # a syntactically valid move.
        try:
            for r in range(6):
                for c in range(6):
                    if not you[r][c] and not opponent[r][c]:
                        return f"{r + 1},{c + 1},0,L"
        except Exception:
            pass
        return "1,1,0,L"
