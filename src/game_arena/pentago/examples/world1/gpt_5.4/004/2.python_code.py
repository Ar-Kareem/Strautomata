
import math

def policy(you, opponent) -> str:
    you_b = [[1 if you[r][c] else 0 for c in range(6)] for r in range(6)]
    opp_b = [[1 if opponent[r][c] else 0 for c in range(6)] for r in range(6)]

    def empty_cells(yb, ob):
        cells = []
        for r in range(6):
            for c in range(6):
                if yb[r][c] == 0 and ob[r][c] == 0:
                    cells.append((r, c))
        return cells

    def rotate_pos_in_quad(lr, lc, dirc):
        if dirc == 'R':
            return lc, 2 - lr
        else:
            return 2 - lc, lr

    def rotate_quad(yb, ob, quad, dirc):
        rs = 0 if quad < 2 else 3
        cs = 0 if quad % 2 == 0 else 3

        ysub = [[yb[rs + i][cs + j] for j in range(3)] for i in range(3)]
        osub = [[ob[rs + i][cs + j] for j in range(3)] for i in range(3)]

        ny = [[0] * 3 for _ in range(3)]
        no = [[0] * 3 for _ in range(3)]

        for i in range(3):
            for j in range(3):
                ni, nj = rotate_pos_in_quad(i, j, dirc)
                ny[ni][nj] = ysub[i][j]
                no[ni][nj] = osub[i][j]

        newy = [row[:] for row in yb]
        newo = [row[:] for row in ob]
        for i in range(3):
            for j in range(3):
                newy[rs + i][cs + j] = ny[i][j]
                newo[rs + i][cs + j] = no[i][j]
        return newy, newo

    def apply_move(yb, ob, move, us=True):
        r, c, q, d = move
        newy = [row[:] for row in yb]
        newo = [row[:] for row in ob]
        if us:
            newy[r][c] = 1
        else:
            newo[r][c] = 1
        return rotate_quad(newy, newo, q, d)

    def lines():
        out = []
        for r in range(6):
            out.append([(r, c) for c in range(6)])
        for c in range(6):
            out.append([(r, c) for r in range(6)])
        for start_c in range(6):
            diag = []
            r, c = 0, start_c
            while r < 6 and c < 6:
                diag.append((r, c))
                r += 1
                c += 1
            if len(diag) >= 5:
                out.append(diag)
        for start_r in range(1, 6):
            diag = []
            r, c = start_r, 0
            while r < 6 and c < 6:
                diag.append((r, c))
                r += 1
                c += 1
            if len(diag) >= 5:
                out.append(diag)
        for start_c in range(6):
            diag = []
            r, c = 0, start_c
            while r < 6 and c >= 0:
                diag.append((r, c))
                r += 1
                c -= 1
            if len(diag) >= 5:
                out.append(diag)
        for start_r in range(1, 6):
            diag = []
            r, c = start_r, 5
            while r < 6 and c >= 0:
                diag.append((r, c))
                r += 1
                c -= 1
            if len(diag) >= 5:
                out.append(diag)
        return out

    ALL_LINES = lines()

    def has_five(board):
        for line in ALL_LINES:
            streak = 0
            for r, c in line:
                if board[r][c]:
                    streak += 1
                    if streak >= 5:
                        return True
                else:
                    streak = 0
        return False

    def outcome_after_our_move(yb, ob):
        yw = has_five(yb)
        ow = has_five(ob)
        if yw and ow:
            return 0
        if yw:
            return 1
        if ow:
            return -1
        full = True
        for r in range(6):
            for c in range(6):
                if yb[r][c] == 0 and ob[r][c] == 0:
                    full = False
                    break
            if not full:
                break
        if full:
            return 0
        return None

    def legal_moves(yb, ob):
        moves = []
        for r, c in empty_cells(yb, ob):
            for q in range(4):
                moves.append((r, c, q, 'L'))
                moves.append((r, c, q, 'R'))
        return moves

    def segment_score(myc, oppc, empties):
        if myc > 0 and oppc > 0:
            return 0
        if myc == 5:
            return 1000000
        if oppc == 5:
            return -1000000
        if myc > 0:
            if myc == 4 and empties == 1:
                return 20000
            if myc == 3 and empties == 2:
                return 1200
            if myc == 2 and empties == 3:
                return 120
            if myc == 1 and empties == 4:
                return 10
        if oppc > 0:
            if oppc == 4 and empties == 1:
                return -25000
            if oppc == 3 and empties == 2:
                return -1600
            if oppc == 2 and empties == 3:
                return -140
            if oppc == 1 and empties == 4:
                return -12
        return 0

    def heuristic(yb, ob):
        if has_five(yb) and has_five(ob):
            return 0
        if has_five(yb):
            return 10**9
        if has_five(ob):
            return -10**9

        score = 0

        center_weights = [
            [3, 4, 5, 5, 4, 3],
            [4, 6, 7, 7, 6, 4],
            [5, 7, 8, 8, 7, 5],
            [5, 7, 8, 8, 7, 5],
            [4, 6, 7, 7, 6, 4],
            [3, 4, 5, 5, 4, 3],
        ]
        for r in range(6):
            for c in range(6):
                if yb[r][c]:
                    score += center_weights[r][c]
                elif ob[r][c]:
                    score -= center_weights[r][c]

        for line in ALL_LINES:
            n = len(line)
            for i in range(n - 4):
                cells = line[i:i+5]
                myc = oppc = 0
                for r, c in cells:
                    myc += yb[r][c]
                    oppc += ob[r][c]
                score += segment_score(myc, oppc, 5 - myc - oppc)

            if n == 6:
                myc = oppc = 0
                for r, c in line:
                    myc += yb[r][c]
                    oppc += ob[r][c]
                if myc > 0 and oppc == 0:
                    score += [0, 4, 20, 120, 800, 5000, 20000][myc]
                elif oppc > 0 and myc == 0:
                    score -= [0, 5, 24, 150, 950, 6000, 22000][oppc]

        return score

    def format_move(move):
        r, c, q, d = move
        return f"{r+1},{c+1},{q},{d}"

    moves = legal_moves(you_b, opp_b)
    fallback = moves[0]

    for mv in moves:
        ny, no = apply_move(you_b, opp_b, mv, us=True)
        out = outcome_after_our_move(ny, no)
        if out == 1:
            return format_move(mv)

    opp_immediate_wins_from_current = 0
    for omv in legal_moves(you_b, opp_b):
        ny, no = apply_move(you_b, opp_b, omv, us=False)
        yw = has_five(ny)
        ow = has_five(no)
        if ow and not yw:
            opp_immediate_wins_from_current += 1

    best_move = None
    best_value = -10**18

    for mv in moves:
        ny, no = apply_move(you_b, opp_b, mv, us=True)
        out = outcome_after_our_move(ny, no)
        if out is not None:
            val = 0 if out == 0 else (10**12 if out == 1 else -10**12)
            if val > best_value:
                best_value = val
                best_move = mv
            continue

        opp_moves = legal_moves(ny, no)
        opp_best = -10**18
        opp_winning_replies = 0

        if not opp_moves:
            val = heuristic(ny, no)
        else:
            sampled = opp_moves
            if len(sampled) > 80:
                scored = []
                for omv in sampled:
                    ty, to = apply_move(ny, no, omv, us=False)
                    h = heuristic(ty, to)
                    scored.append((h, omv))
                scored.sort(key=lambda x: x[0])
                sampled = [m for _, m in scored[:40]] + [m for _, m in scored[-40:]]

            for omv in sampled:
                ty, to = apply_move(ny, no, omv, us=False)
                yw = has_five(ty)
                ow = has_five(to)
                if ow and not yw:
                    reply_score = 10**11
                    opp_winning_replies += 1
                elif yw and ow:
                    reply_score = 0
                elif yw:
                    reply_score = -10**10
                else:
                    reply_score = heuristic(ty, to)
                if reply_score > opp_best:
                    opp_best = reply_score

            val = heuristic(ny, no) - opp_best
            val -= opp_winning_replies * 5000000

        if opp_immediate_wins_from_current > 0:
            blockers = 0
            for omv in legal_moves(ny, no):
                ty, to = apply_move(ny, no, omv, us=False)
                yw = has_five(ty)
                ow = has_five(to)
                if ow and not yw:
                    blockers += 1
                    if blockers >= 2:
                        break
            val -= blockers * 2000000

        if val > best_value:
            best_value = val
            best_move = mv

    if best_move is None:
        best_move = fallback
    return format_move(best_move)
