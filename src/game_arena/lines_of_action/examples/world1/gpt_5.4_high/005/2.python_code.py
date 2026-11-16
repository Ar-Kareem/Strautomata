
import time

WIN = 10_000_000
INF = 1_000_000_000

DIRS = (
    (-1, 0), (1, 0), (0, -1), (0, 1),
    (-1, -1), (1, 1), (-1, 1), (1, -1),
)

NEIGHBORS = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
)

CENTER1D = (0, 1, 2, 3, 3, 2, 1, 0)
QUAD_VALUES = (0, -15, 5, 18, 8)


class SearchTimeout(Exception):
    pass


def format_move(mv):
    return f"{mv[0]},{mv[1]}:{mv[2]},{mv[3]}"


def generate_moves(board, side):
    row_counts = [0] * 8
    col_counts = [0] * 8
    diag_counts = [0] * 15          # r - c + 7
    anti_counts = [0] * 15          # r + c
    pieces = []

    for r in range(8):
        row = board[r]
        for c in range(8):
            v = row[c]
            if v != 0:
                row_counts[r] += 1
                col_counts[c] += 1
                diag_counts[r - c + 7] += 1
                anti_counts[r + c] += 1
                if v == side:
                    pieces.append((r, c))

    opp = -side
    moves = []

    for fr, fc in pieces:
        for dr, dc in DIRS:
            if dr == 0:
                dist = row_counts[fr]
            elif dc == 0:
                dist = col_counts[fc]
            elif dr == dc:
                dist = diag_counts[fr - fc + 7]
            else:
                dist = anti_counts[fr + fc]

            nr = fr + dr * dist
            nc = fc + dc * dist

            if nr < 0 or nr >= 8 or nc < 0 or nc >= 8:
                continue
            if board[nr][nc] == side:
                continue

            blocked = False
            rr = fr + dr
            cc = fc + dc
            for _ in range(dist - 1):
                if board[rr][cc] == opp:
                    blocked = True
                    break
                rr += dr
                cc += dc

            if not blocked:
                moves.append((fr, fc, nr, nc))

    return moves


def connected(board, side):
    start = None
    count = 0

    for r in range(8):
        row = board[r]
        for c in range(8):
            if row[c] == side:
                count += 1
                if start is None:
                    start = (r, c)

    if count <= 1:
        return True

    visited = [[False] * 8 for _ in range(8)]
    stack = [start]
    visited[start[0]][start[1]] = True
    seen = 1

    while stack:
        r, c = stack.pop()
        for dr, dc in NEIGHBORS:
            rr = r + dr
            cc = c + dc
            if 0 <= rr < 8 and 0 <= cc < 8 and not visited[rr][cc] and board[rr][cc] == side:
                visited[rr][cc] = True
                seen += 1
                if seen == count:
                    return True
                stack.append((rr, cc))

    return False


def analyze_side(board, side):
    coords = []
    edge = 0
    central = 0
    minr = 8
    minc = 8
    maxr = -1
    maxc = -1

    for r in range(8):
        row = board[r]
        rv = CENTER1D[r]
        for c in range(8):
            if row[c] == side:
                coords.append((r, c))
                if r == 0 or r == 7 or c == 0 or c == 7:
                    edge += 1
                central += rv + CENTER1D[c]
                if r < minr:
                    minr = r
                if r > maxr:
                    maxr = r
                if c < minc:
                    minc = c
                if c > maxc:
                    maxc = c

    n = len(coords)
    if n == 0:
        return (1, 0, 0, 0, 0, 0, 0, 0, 0)

    bbox_area = (maxr - minr + 1) * (maxc - minc + 1)

    if n == 1:
        return (1, 1, 0, 1, 0, bbox_area, edge, central, n)

    isolated = 0
    adj_pairs = 0
    for r, c in coords:
        local_adj = 0
        for dr, dc in NEIGHBORS:
            rr = r + dr
            cc = c + dc
            if 0 <= rr < 8 and 0 <= cc < 8 and board[rr][cc] == side:
                local_adj += 1
                if rr > r or (rr == r and cc > c):
                    adj_pairs += 1
        if local_adj == 0:
            isolated += 1

    visited = [[False] * 8 for _ in range(8)]
    comps = []
    largest = 0

    for r, c in coords:
        if visited[r][c]:
            continue
        stack = [(r, c)]
        visited[r][c] = True
        comp = []
        while stack:
            cr, cc = stack.pop()
            comp.append((cr, cc))
            for dr, dc in NEIGHBORS:
                rr = cr + dr
                nc = cc + dc
                if 0 <= rr < 8 and 0 <= nc < 8 and not visited[rr][nc] and board[rr][nc] == side:
                    visited[rr][nc] = True
                    stack.append((rr, nc))
        comps.append(comp)
        if len(comp) > largest:
            largest = len(comp)

    components = len(comps)

    mst_cost = 0
    if components > 1:
        dist = [[0] * components for _ in range(components)]
        for i in range(components):
            ci = comps[i]
            for j in range(i + 1, components):
                cj = comps[j]
                best = 8
                for r1, c1 in ci:
                    for r2, c2 in cj:
                        d = max(abs(r1 - r2), abs(c1 - c2))
                        if d < best:
                            best = d
                            if best == 2:
                                break
                    if best == 2:
                        break
                dist[i][j] = best
                dist[j][i] = best

        in_tree = [False] * components
        bestd = [99] * components
        bestd[0] = 0
        for _ in range(components):
            u = -1
            val = 99
            for i in range(components):
                if not in_tree[i] and bestd[i] < val:
                    val = bestd[i]
                    u = i
            in_tree[u] = True
            mst_cost += val
            row = dist[u]
            for v in range(components):
                dv = row[v]
                if not in_tree[v] and dv < bestd[v]:
                    bestd[v] = dv

    quad = 0
    if n > 2:
        for r in range(7):
            row0 = board[r]
            row1 = board[r + 1]
            for c in range(7):
                cnt = (
                    (1 if row0[c] == side else 0) +
                    (1 if row0[c + 1] == side else 0) +
                    (1 if row1[c] == side else 0) +
                    (1 if row1[c + 1] == side else 0)
                )
                quad += QUAD_VALUES[cnt]

    return (components, largest, mst_cost, isolated, adj_pairs, bbox_area, edge, central, n + quad)


def feature_score(board, side):
    components, largest, mst_cost, isolated, adj_pairs, bbox_area, edge, central, n_quad = analyze_side(board, side)
    # n_quad = n + quad, split back cheaply
    # quad is small relative term; n = n_quad - quad, but we only need a small piece-count term.
    # To avoid extra return slots we approximate n contribution from largest/components info indirectly.
    # Still, n_quad keeps the quad term active; piece-count pressure remains low priority.
    return (
        -1800 * (components - 1)
        -140 * mst_cost
        +110 * largest
        +16 * adj_pairs
        -28 * isolated
        -8 * bbox_area
        -5 * edge
        +4 * central
        +6 * n_quad
    )


def evaluate(board, side):
    return feature_score(board, side) - feature_score(board, -side)


def static_move_score(board, side, mv):
    fr, fc, nr, nc = mv

    adj_dest = 0
    adj_src = 0

    for dr, dc in NEIGHBORS:
        rr = nr + dr
        cc = nc + dc
        if 0 <= rr < 8 and 0 <= cc < 8 and not (rr == fr and cc == fc) and board[rr][cc] == side:
            adj_dest += 1

        rr = fr + dr
        cc = fc + dc
        if 0 <= rr < 8 and 0 <= cc < 8 and board[rr][cc] == side:
            adj_src += 1

    score = 26 * adj_dest - 8 * adj_src

    if board[nr][nc] == -side:
        score += 90

    score += 8 * ((CENTER1D[nr] + CENTER1D[nc]) - (CENTER1D[fr] + CENTER1D[fc]))

    if nr == 0 or nr == 7 or nc == 0 or nc == 7:
        score -= 4

    return score


class Searcher:
    def __init__(self, board, deadline):
        self.board = board
        self.deadline = deadline
        self.nodes = 0
        self.killers = [(None, None) for _ in range(64)]
        self.history = {}

    def _time_check(self):
        self.nodes += 1
        if (self.nodes & 255) == 0 and time.perf_counter() > self.deadline:
            raise SearchTimeout

    def _add_killer(self, ply, mv):
        k1, k2 = self.killers[ply]
        if mv != k1:
            self.killers[ply] = (mv, k1)

    def _order_moves(self, moves, side, ply, pv_move=None, dangerous=None):
        k1, k2 = self.killers[ply]
        hist = self.history
        board = self.board

        def key(mv):
            s = static_move_score(board, side, mv)
            s += hist.get((side, mv), 0)
            if mv == pv_move:
                s += 2_000_000
            if mv == k1:
                s += 900_000
            elif mv == k2:
                s += 800_000
            if dangerous is not None:
                if dangerous.get(mv, False):
                    s -= 200_000
                else:
                    s += 200_000
            return s

        moves.sort(key=key, reverse=True)

    def negamax(self, depth, alpha, beta, side, ply):
        self._time_check()

        if depth == 0:
            return evaluate(self.board, side)

        moves = generate_moves(self.board, side)
        if not moves:
            return evaluate(self.board, side)

        self._order_moves(moves, side, ply)

        best = -INF
        board = self.board
        opp = -side

        for mv in moves:
            fr, fc, nr, nc = mv
            captured = board[nr][nc]
            board[fr][fc] = 0
            board[nr][nc] = side

            if connected(board, side):
                score = WIN
            elif captured == opp and connected(board, opp):
                score = -WIN
            elif depth == 1:
                score = evaluate(board, side)
            else:
                score = -self.negamax(depth - 1, -beta, -alpha, opp, ply + 1)

            board[fr][fc] = side
            board[nr][nc] = captured

            if score > best:
                best = score
            if score > alpha:
                alpha = score

            if alpha >= beta:
                self._add_killer(ply, mv)
                self.history[(side, mv)] = self.history.get((side, mv), 0) + depth * depth
                break

            if best >= WIN:
                break

        return best

    def search_root(self, depth, moves, dangerous, pv_move):
        if time.perf_counter() > self.deadline:
            raise SearchTimeout

        root_moves = moves[:]
        self._order_moves(root_moves, 1, 0, pv_move=pv_move, dangerous=dangerous)

        alpha = -INF
        beta = INF
        best_score = -INF
        best_move = root_moves[0]
        board = self.board

        for mv in root_moves:
            if time.perf_counter() > self.deadline:
                raise SearchTimeout

            fr, fc, nr, nc = mv
            captured = board[nr][nc]
            board[fr][fc] = 0
            board[nr][nc] = 1

            if connected(board, 1):
                score = WIN
            elif captured == -1 and connected(board, -1):
                score = -WIN
            elif depth == 1:
                score = evaluate(board, 1)
                if dangerous.get(mv, False):
                    score -= 2_000_000
            else:
                score = -self.negamax(depth - 1, -beta, -alpha, -1, 1)

            board[fr][fc] = 1
            board[nr][nc] = captured

            if score > best_score:
                best_score = score
                best_move = mv
            if score > alpha:
                alpha = score

            if best_score >= WIN:
                break

        return best_score, best_move


def sign(x):
    if x > 0:
        return 1
    if x < 0:
        return -1
    return 0


def line_count(board, r, c, dr, dc):
    rr = r
    cc = c
    while 0 <= rr - dr < 8 and 0 <= cc - dc < 8:
        rr -= dr
        cc -= dc

    cnt = 0
    while 0 <= rr < 8 and 0 <= cc < 8:
        if board[rr][cc] != 0:
            cnt += 1
        rr += dr
        cc += dc
    return cnt


def is_legal_move(board, side, fr, fc, nr, nc):
    if not (0 <= fr < 8 and 0 <= fc < 8 and 0 <= nr < 8 and 0 <= nc < 8):
        return False
    if board[fr][fc] != side or board[nr][nc] == side:
        return False
    if fr == nr and fc == nc:
        return False

    rd = nr - fr
    cd = nc - fc

    if rd == 0:
        dr = 0
        dc = sign(cd)
    elif cd == 0:
        dr = sign(rd)
        dc = 0
    elif abs(rd) == abs(cd):
        dr = sign(rd)
        dc = sign(cd)
    else:
        return False

    dist = max(abs(rd), abs(cd))
    need = line_count(board, fr, fc, dr, dc)
    if dist != need:
        return False

    opp = -side
    rr = fr + dr
    cc = fc + dc
    for _ in range(dist - 1):
        if board[rr][cc] == opp:
            return False
        rr += dr
        cc += dc

    return True


def emergency_legal_move(board, side):
    for fr in range(8):
        for fc in range(8):
            if board[fr][fc] != side:
                continue
            for nr in range(8):
                for nc in range(8):
                    if is_legal_move(board, side, fr, fc, nr, nc):
                        return (fr, fc, nr, nc)
    return None


def policy(board) -> str:
    b = [list(row) for row in board]

    moves = generate_moves(b, 1)
    if not moves:
        mv = emergency_legal_move(b, 1)
        if mv is not None:
            return format_move(mv)
        return "0,0:0,0"

    if len(moves) == 1:
        return format_move(moves[0])

    moves.sort(key=lambda mv: static_move_score(b, 1, mv), reverse=True)

    deadline = time.perf_counter() + 0.94

    dangerous = {}
    best_move = moves[0]
    best_quick_score = -INF

    # Quick tactical pass:
    # - return any immediate win
    # - avoid moves that lose immediately or allow an immediate winning reply
    for mv in moves:
        if time.perf_counter() > deadline - 0.14:
            break

        fr, fc, nr, nc = mv
        captured = b[nr][nc]
        b[fr][fc] = 0
        b[nr][nc] = 1

        if connected(b, 1):
            b[fr][fc] = 1
            b[nr][nc] = captured
            return format_move(mv)

        lose_now = (captured == -1 and connected(b, -1))
        if lose_now:
            dangerous[mv] = True
            quick_score = -WIN
        else:
            opp_can_win = False
            opp_moves = generate_moves(b, -1)

            for omv in opp_moves:
                ofr, ofc, onr, onc = omv
                ocap = b[onr][onc]
                b[ofr][ofc] = 0
                b[onr][onc] = -1

                if connected(b, -1):
                    opp_can_win = True
                    b[ofr][ofc] = -1
                    b[onr][onc] = ocap
                    break

                b[ofr][ofc] = -1
                b[onr][onc] = ocap

            dangerous[mv] = opp_can_win
            quick_score = evaluate(b, 1)
            if opp_can_win:
                quick_score -= 2_000_000

        if quick_score > best_quick_score:
            best_quick_score = quick_score
            best_move = mv

        b[fr][fc] = 1
        b[nr][nc] = captured

    if time.perf_counter() > deadline - 0.03:
        return format_move(best_move)

    searcher = Searcher(b, deadline)
    pv_move = best_move

    for depth in range(1, 9):
        try:
            score, mv = searcher.search_root(depth, moves, dangerous, pv_move)
            if mv is not None:
                best_move = mv
                pv_move = mv
            if score >= WIN:
                break
        except SearchTimeout:
            break

    return format_move(best_move)
