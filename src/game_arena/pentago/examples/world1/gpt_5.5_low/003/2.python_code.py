
# Pentago policy
# Return format: "row,col,quad,dir"

def policy(you, opponent) -> str:
    # ---------- helpers ----------
    def make_board():
        b = [[0] * 6 for _ in range(6)]
        for r in range(6):
            for c in range(6):
                if int(you[r][c]):
                    b[r][c] = 1
                elif int(opponent[r][c]):
                    b[r][c] = -1
        return b

    def rotate_in_place(b, q, d):
        r0 = 0 if q < 2 else 3
        c0 = 0 if q % 2 == 0 else 3

        sub = [[b[r0 + i][c0 + j] for j in range(3)] for i in range(3)]

        if d == "R":
            for i in range(3):
                for j in range(3):
                    b[r0 + i][c0 + j] = sub[2 - j][i]
        else:
            for i in range(3):
                for j in range(3):
                    b[r0 + i][c0 + j] = sub[j][2 - i]

    def apply_move(b, r, c, q, d, player):
        nb = [row[:] for row in b]
        nb[r][c] = player
        rotate_in_place(nb, q, d)
        return nb

    def has_win(b, player):
        for line in LINES:
            ok = True
            for r, c in line:
                if b[r][c] != player:
                    ok = False
                    break
            if ok:
                return True
        return False

    def legal_moves(b):
        moves = []
        for r in range(6):
            for c in range(6):
                if b[r][c] == 0:
                    for q in range(4):
                        moves.append((r, c, q, "L"))
                        moves.append((r, c, q, "R"))
        return moves

    def static_eval(b):
        # Positive is good for us.
        score = 0

        # Positional preference: center and near-center are valuable.
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
                score += weights[r][c] * b[r][c]

        # Line pattern scoring.
        # A 5-cell window with only one player's stones is important.
        vals = [0, 2, 12, 70, 700, 100000]
        for line in LINES:
            mine = 0
            theirs = 0
            for r, c in line:
                if b[r][c] == 1:
                    mine += 1
                elif b[r][c] == -1:
                    theirs += 1

            if mine and not theirs:
                score += vals[mine]
            elif theirs and not mine:
                # Defensive bias: block opponent threats aggressively.
                score -= int(vals[theirs] * 1.25)

        return score

    def move_to_str(m):
        r, c, q, d = m
        return f"{r + 1},{c + 1},{q},{d}"

    # ---------- precompute all 5-cell winning windows ----------
    # Stored as a function attribute so repeated calls in an arena are cheaper.
    if not hasattr(policy, "_LINES"):
        lines = []

        dirs = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for r in range(6):
            for c in range(6):
                for dr, dc in dirs:
                    rr = r + 4 * dr
                    cc = c + 4 * dc
                    if 0 <= rr < 6 and 0 <= cc < 6:
                        lines.append(tuple((r + k * dr, c + k * dc) for k in range(5)))

        policy._LINES = lines

    LINES = policy._LINES

    board = make_board()
    moves = legal_moves(board)

    # Absolute fallback: first legal move.
    fallback = move_to_str(moves[0])

    # Opening preference: if the board is empty or nearly empty, occupy a strong central cell.
    occupied = sum(1 for r in range(6) for c in range(6) if board[r][c] != 0)
    if occupied <= 1:
        for r, c in [(2, 2), (2, 3), (3, 2), (3, 3)]:
            if board[r][c] == 0:
                return f"{r + 1},{c + 1},0,R"

    scored = []
    best_draw = None
    best_any = None
    best_any_score = -10**18

    # ---------- immediate win / evaluate all own moves ----------
    for m in moves:
        r, c, q, d = m
        nb = apply_move(board, r, c, q, d, 1)

        my_win = has_win(nb, 1)
        opp_win = has_win(nb, -1)

        # Winning move beats everything, unless it is simultaneous draw.
        if my_win and not opp_win:
            return move_to_str(m)

        if my_win and opp_win:
            if best_draw is None:
                best_draw = m
            continue

        # Never like a move that gives opponent an immediate completed five.
        if opp_win and not my_win:
            sc = -10**12 + static_eval(nb)
        else:
            sc = static_eval(nb)

        # Small deterministic tie-breakers favor central placements.
        sc += (5 - abs(2.5 - r) - abs(2.5 - c))

        scored.append((sc, m, nb))

        if sc > best_any_score:
            best_any_score = sc
            best_any = m

    if not scored:
        if best_draw is not None:
            return move_to_str(best_draw)
        return fallback

    scored.sort(reverse=True, key=lambda x: x[0])

    # ---------- tactical safety check ----------
    # Prefer a strong move that does not allow the opponent to win immediately.
    # Check all candidates if possible; the branching factor is at most 288, which is fine.
    safe_best = None
    safe_score = -10**18

    for sc, m, nb in scored:
        # If this move already leaves an opponent win, skip it.
        if has_win(nb, -1):
            continue

        opp_can_win = False
        opp_moves = legal_moves(nb)

        for om in opp_moves:
            orr, occ, oq, od = om
            ob = apply_move(nb, orr, occ, oq, od, -1)
            ow = has_win(ob, -1)
            mw = has_win(ob, 1)

            # Opponent wants a real win, not a simultaneous draw.
            if ow and not mw:
                opp_can_win = True
                break

        if not opp_can_win:
            if sc > safe_score:
                safe_score = sc
                safe_best = m

            # Since scored is sorted, the first safe move is usually best enough.
            return move_to_str(m)

    # If every move appears to allow a tactic, take a draw if available.
    if best_draw is not None:
        return move_to_str(best_draw)

    # Otherwise return the highest-scoring legal move.
    if best_any is not None:
        return move_to_str(best_any)

    return fallback
