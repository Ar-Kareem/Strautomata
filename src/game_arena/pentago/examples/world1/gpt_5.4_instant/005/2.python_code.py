
import math

def policy(you, opponent) -> str:
    # Convert to plain int lists
    Y = [[1 if you[r][c] else 0 for c in range(6)] for r in range(6)]
    O = [[1 if opponent[r][c] else 0 for c in range(6)] for r in range(6)]

    # ---------- Board helpers ----------
    QUAD_SLICES = {
        0: (0, 3, 0, 3),
        1: (0, 3, 3, 6),
        2: (3, 6, 0, 3),
        3: (3, 6, 3, 6),
    }

    def rotate3(mat, quad, direction):
        r0, r1, c0, c1 = QUAD_SLICES[quad]
        sub = [row[c0:c1] for row in mat[r0:r1]]
        out = [row[:] for row in mat]
        if direction == 'R':
            rot = [[sub[2 - j][i] for j in range(3)] for i in range(3)]
        else:  # 'L'
            rot = [[sub[j][2 - i] for j in range(3)] for i in range(3)]
        for i in range(3):
            for j in range(3):
                out[r0 + i][c0 + j] = rot[i][j]
        return out

    def apply_move(yb, ob, move, for_you=True):
        r, c, q, d = move
        ny = [row[:] for row in yb]
        no = [row[:] for row in ob]
        if for_you:
            ny[r][c] = 1
        else:
            no[r][c] = 1
        ny = rotate3(ny, q, d)
        no = rotate3(no, q, d)
        return ny, no

    def all_lines(board):
        lines = []
        # Rows
        for r in range(6):
            lines.append(board[r][:])
        # Cols
        for c in range(6):
            lines.append([board[r][c] for r in range(6)])
        # Diagonals length >= 5
        # down-right
        starts = [(0, 0), (0, 1), (1, 0)]
        for sr, sc in starts:
            line = []
            r, c = sr, sc
            while r < 6 and c < 6:
                line.append(board[r][c])
                r += 1
                c += 1
            if len(line) >= 5:
                lines.append(line)
        # down-left
        starts = [(0, 5), (0, 4), (1, 5)]
        for sr, sc in starts:
            line = []
            r, c = sr, sc
            while r < 6 and c >= 0:
                line.append(board[r][c])
                r += 1
                c -= 1
            if len(line) >= 5:
                lines.append(line)
        return lines

    def has_five(board):
        for line in all_lines(board):
            run = 0
            for v in line:
                if v:
                    run += 1
                    if run >= 5:
                        return True
                else:
                    run = 0
        return False

    def outcome_after_our_move(yb, ob, move):
        ny, no = apply_move(yb, ob, move, True)
        yw = has_five(ny)
        ow = has_five(no)
        if yw and ow:
            return 0  # draw
        if yw:
            return 1  # win
        if ow:
            return -1  # loss-like state after our move
        full = True
        for r in range(6):
            for c in range(6):
                if ny[r][c] == 0 and no[r][c] == 0:
                    full = False
                    break
            if not full:
                break
        if full:
            return 0
        return None

    def legal_moves(yb, ob):
        moves = []
        for r in range(6):
            for c in range(6):
                if yb[r][c] == 0 and ob[r][c] == 0:
                    for q in range(4):
                        moves.append((r, c, q, 'L'))
                        moves.append((r, c, q, 'R'))
        return moves

    # ---------- Evaluation ----------
    CENTER_WEIGHT = [
        [0, 1, 2, 2, 1, 0],
        [1, 2, 3, 3, 2, 1],
        [2, 3, 4, 4, 3, 2],
        [2, 3, 4, 4, 3, 2],
        [1, 2, 3, 3, 2, 1],
        [0, 1, 2, 2, 1, 0],
    ]

    def line_windows(line, k=5):
        for i in range(len(line) - k + 1):
            yield line[i:i + k]

    def evaluate_board(yb, ob):
        yw = has_five(yb)
        ow = has_five(ob)
        if yw and ow:
            return 0
        if yw:
            return 1000000
        if ow:
            return -1000000

        score = 0

        # Placement centrality
        for r in range(6):
            for c in range(6):
                if yb[r][c]:
                    score += CENTER_WEIGHT[r][c] * 2
                elif ob[r][c]:
                    score -= CENTER_WEIGHT[r][c] * 2

        # Analyze all 5-length windows in rows/cols/diags
        lines_y = all_lines(yb)
        lines_o = all_lines(ob)

        for ly, lo in zip(lines_y, lines_o):
            n = len(ly)
            for i in range(n - 4):
                wy = ly[i:i+5]
                wo = lo[i:i+5]
                cy = sum(wy)
                co = sum(wo)
                if cy and co:
                    continue
                if cy:
                    if cy == 4:
                        score += 1500
                    elif cy == 3:
                        score += 180
                    elif cy == 2:
                        score += 25
                    elif cy == 1:
                        score += 3
                elif co:
                    if co == 4:
                        score -= 1700
                    elif co == 3:
                        score -= 220
                    elif co == 2:
                        score -= 30
                    elif co == 1:
                        score -= 3

        # Reward longer pure segments in full lines
        for ly, lo in zip(lines_y, lines_o):
            # our runs
            run = 0
            for a, b in zip(ly, lo):
                if a == 1 and b == 0:
                    run += 1
                else:
                    if run == 4:
                        score += 500
                    elif run == 3:
                        score += 70
                    elif run == 2:
                        score += 10
                    run = 0
            if run == 4:
                score += 500
            elif run == 3:
                score += 70
            elif run == 2:
                score += 10

            run = 0
            for a, b in zip(ly, lo):
                if b == 1 and a == 0:
                    run += 1
                else:
                    if run == 4:
                        score -= 550
                    elif run == 3:
                        score -= 90
                    elif run == 2:
                        score -= 12
                    run = 0
            if run == 4:
                score -= 550
            elif run == 3:
                score -= 90
            elif run == 2:
                score -= 12

        return score

    def immediate_winning_moves(yb, ob, for_you=True, moves_subset=None):
        wins = []
        moves = moves_subset if moves_subset is not None else legal_moves(yb, ob)
        for mv in moves:
            ny, no = apply_move(yb, ob, mv, for_you)
            yw = has_five(ny)
            ow = has_five(no)
            if for_you:
                if yw and not ow:
                    wins.append(mv)
            else:
                if ow and not yw:
                    wins.append(mv)
        return wins

    # ---------- Move selection ----------
    moves = legal_moves(Y, O)
    fallback = moves[0]

    # 1. Immediate winning move
    my_wins = immediate_winning_moves(Y, O, True, moves)
    if my_wins:
        # Prefer wins with better board score, but any is fine
        best = None
        best_sc = -10**18
        for mv in my_wins:
            ny, no = apply_move(Y, O, mv, True)
            sc = evaluate_board(ny, no)
            if sc > best_sc:
                best_sc = sc
                best = mv
        r, c, q, d = best
        return f"{r+1},{c+1},{q},{d}"

    # Pre-rank candidate moves by static eval to limit deeper work
    ranked = []
    for mv in moves:
        terminal = outcome_after_our_move(Y, O, mv)
        if terminal == -1:
            base = -900000  # avoid accidental self-loss / opponent-only win after rotation
        else:
            ny, no = apply_move(Y, O, mv, True)
            base = evaluate_board(ny, no)
        # slight preference for center placement before rotation
        r, c, q, d = mv
        base += CENTER_WEIGHT[r][c]
        ranked.append((base, mv))
    ranked.sort(reverse=True, key=lambda x: x[0])

    # Keep top candidates for reply search
    top_moves = [mv for _, mv in ranked[:24]]

    best_move = None
    best_value = -10**18

    for mv in top_moves:
        terminal = outcome_after_our_move(Y, O, mv)
        if terminal == -1:
            value = -900000
        else:
            ny, no = apply_move(Y, O, mv, True)

            if terminal == 0:
                value = 0
            else:
                # Opponent immediate wins?
                opp_moves = legal_moves(ny, no)

                # Fast direct check
                opp_win_found = False
                opp_best = -10**18

                # Small move ordering for opponent
                opp_ranked = []
                for omv in opp_moves:
                    nny, nno = apply_move(ny, no, omv, False)
                    yw = has_five(nny)
                    ow = has_five(nno)
                    if ow and not yw:
                        opp_ranked = [(10**12, omv)]
                        opp_win_found = True
                        break
                    sc = evaluate_board(nny, nno)
                    opp_ranked.append((sc, omv))

                if opp_win_found:
                    value = -800000
                else:
                    opp_ranked.sort(reverse=True, key=lambda x: x[0])
                    # Search only top replies
                    limited_opp = [omv for _, omv in opp_ranked[:16]]
                    worst_for_us = 10**18
                    for omv in limited_opp:
                        nny, nno = apply_move(ny, no, omv, False)
                        sc = evaluate_board(nny, nno)
                        if sc < worst_for_us:
                            worst_for_us = sc
                    value = worst_for_us

                    # Bonus if opponent has no immediate winning reply and we create threats
                    my_next_wins = len(immediate_winning_moves(ny, no, True))
                    opp_next_wins = len(immediate_winning_moves(ny, no, False))
                    value += my_next_wins * 1200
                    value -= opp_next_wins * 1800

        if value > best_value:
            best_value = value
            best_move = mv

    if best_move is None:
        best_move = fallback

    r, c, q, d = best_move
    return f"{r+1},{c+1},{q},{d}"
