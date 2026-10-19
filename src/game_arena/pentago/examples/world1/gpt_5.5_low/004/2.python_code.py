
# Pentago policy
# Implements: policy(you, opponent) -> str

LINES = []

def _init_lines():
    global LINES
    if LINES:
        return

    dirs = [(0, 1), (1, 0), (1, 1), (1, -1)]
    for r in range(6):
        for c in range(6):
            for dr, dc in dirs:
                cells = []
                rr, cc = r, c
                while 0 <= rr < 6 and 0 <= cc < 6:
                    cells.append((rr, cc))
                    rr += dr
                    cc += dc
                if len(cells) >= 5:
                    for i in range(len(cells) - 4):
                        LINES.append(cells[i:i + 5])


def _copy_board(b):
    return [list(row) for row in b]


def _has_win(b):
    _init_lines()
    for line in LINES:
        ok = True
        for r, c in line:
            if not b[r][c]:
                ok = False
                break
        if ok:
            return True
    return False


def _rotate_quad(a, b, q, d):
    r0 = 0 if q < 2 else 3
    c0 = 0 if q % 2 == 0 else 3

    olda = [[a[r0 + i][c0 + j] for j in range(3)] for i in range(3)]
    oldb = [[b[r0 + i][c0 + j] for j in range(3)] for i in range(3)]

    for i in range(3):
        for j in range(3):
            if d == "R":
                ni, nj = j, 2 - i
            else:
                ni, nj = 2 - j, i
            a[r0 + ni][c0 + nj] = olda[i][j]
            b[r0 + ni][c0 + nj] = oldb[i][j]


def _apply_move(you, opp, r, c, q, d):
    y = _copy_board(you)
    o = _copy_board(opp)
    y[r][c] = 1
    _rotate_quad(y, o, q, d)
    return y, o


def _legal_moves(you, opp):
    moves = []
    for r in range(6):
        for c in range(6):
            if not you[r][c] and not opp[r][c]:
                for q in range(4):
                    moves.append((r, c, q, "L"))
                    moves.append((r, c, q, "R"))
    return moves


def _move_to_str(m):
    r, c, q, d = m
    return str(r + 1) + "," + str(c + 1) + "," + str(q) + "," + d


def _terminal_result(you, opp):
    yw = _has_win(you)
    ow = _has_win(opp)
    if yw and not ow:
        return 1
    if ow and not yw:
        return -1
    if yw and ow:
        return 0
    return None


def _heuristic(you, opp):
    _init_lines()

    score = 0

    # Line evaluation.
    # Strongly reward open friendly lines and strongly punish open enemy lines.
    my_val = [0, 2, 12, 80, 1200, 100000]
    op_val = [0, 2, 14, 100, 1600, 100000]

    for line in LINES:
        yc = 0
        oc = 0
        for r, c in line:
            if you[r][c]:
                yc += 1
            elif opp[r][c]:
                oc += 1

        if yc and oc:
            continue
        if yc:
            score += my_val[yc]
        elif oc:
            score -= op_val[oc]

    # Positional preference: center and near-center cells are flexible in Pentago.
    weights = [
        [1, 2, 3, 3, 2, 1],
        [2, 4, 5, 5, 4, 2],
        [3, 5, 7, 7, 5, 3],
        [3, 5, 7, 7, 5, 3],
        [2, 4, 5, 5, 4, 2],
        [1, 2, 3, 3, 2, 1],
    ]

    for r in range(6):
        for c in range(6):
            if you[r][c]:
                score += weights[r][c]
            elif opp[r][c]:
                score -= weights[r][c]

    return score


def _opponent_has_immediate_win(you, opp):
    # In this position, opponent is to move.
    # Return True only if opponent can force an exclusive win next move.
    for m in _legal_moves(opp, you):
        r, c, q, d = m
        no, ny = _apply_move(opp, you, r, c, q, d)
        res = _terminal_result(no, ny)
        if res == 1:
            return True
    return False


def policy(you, opponent) -> str:
    _init_lines()

    # Normalize input to ordinary Python lists.
    you = [[int(you[r][c]) for c in range(6)] for r in range(6)]
    opponent = [[int(opponent[r][c]) for c in range(6)] for r in range(6)]

    moves = _legal_moves(you, opponent)

    # Absolute fallback, should always be legal because at least one empty cell exists.
    fallback = moves[0]

    scored = []
    best_move = fallback
    best_score = -10 ** 18

    # 1. Immediate winning move.
    # Prefer exclusive wins; remember drawing wins only as fallback.
    draw_win = None
    for m in moves:
        r, c, q, d = m
        ny, no = _apply_move(you, opponent, r, c, q, d)
        res = _terminal_result(ny, no)

        if res == 1:
            return _move_to_str(m)
        if res == 0 and _has_win(ny):
            draw_win = m

        h = _heuristic(ny, no)
        scored.append((h, m, ny, no))
        if h > best_score:
            best_score = h
            best_move = m

    # 2. Sort by heuristic, then look for a good move that does not allow
    # opponent an immediate exclusive win.
    scored.sort(key=lambda x: x[0], reverse=True)

    safe_best = None
    safe_best_score = -10 ** 18

    for h, m, ny, no in scored:
        if not _opponent_has_immediate_win(ny, no):
            safe_best = m
            safe_best_score = h
            break

    if safe_best is not None:
        return _move_to_str(safe_best)

    # 3. If all moves appear unsafe, a draw-producing move is better than many losses.
    if draw_win is not None:
        return _move_to_str(draw_win)

    # 4. Final guaranteed legal fallback.
    return _move_to_str(best_move)
