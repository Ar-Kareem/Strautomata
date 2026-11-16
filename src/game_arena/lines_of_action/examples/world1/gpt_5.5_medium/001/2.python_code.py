
import time

DIRS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1)
]

INF = 10 ** 12
WIN = 10 ** 9


def policy(board) -> str:
    start_time = time.time()
    end_time = start_time + 0.90

    B = [[int(board[r][c]) for c in range(8)] for r in range(8)]

    class Timeout(Exception):
        pass

    nodes = 0

    def inside(r, c):
        return 0 <= r < 8 and 0 <= c < 8

    def count_pieces(side):
        total = 0
        for r in range(8):
            for c in range(8):
                if B[r][c] == side:
                    total += 1
        return total

    def line_count(r, c, dr, dc):
        total = 1
        rr, cc = r + dr, c + dc
        while inside(rr, cc):
            if B[rr][cc] != 0:
                total += 1
            rr += dr
            cc += dc

        rr, cc = r - dr, c - dc
        while inside(rr, cc):
            if B[rr][cc] != 0:
                total += 1
            rr -= dr
            cc -= dc

        return total

    def generate_moves(side):
        enemy = -side
        moves = []

        for r in range(8):
            for c in range(8):
                if B[r][c] != side:
                    continue

                for dr, dc in DIRS:
                    dist = line_count(r, c, dr, dc)
                    tr = r + dr * dist
                    tc = c + dc * dist

                    if not inside(tr, tc):
                        continue
                    if B[tr][tc] == side:
                        continue

                    blocked = False
                    for k in range(1, dist):
                        rr = r + dr * k
                        cc = c + dc * k
                        if B[rr][cc] == enemy:
                            blocked = True
                            break

                    if not blocked:
                        moves.append((r, c, tr, tc, B[tr][tc]))

        return moves

    def make_move(m, side):
        fr, fc, tr, tc, cap = m
        B[fr][fc] = 0
        B[tr][tc] = side

    def undo_move(m, side):
        fr, fc, tr, tc, cap = m
        B[fr][fc] = side
        B[tr][tc] = cap

    def is_connected(side):
        pieces = []
        for r in range(8):
            for c in range(8):
                if B[r][c] == side:
                    pieces.append((r, c))

        n = len(pieces)
        if n == 0:
            return False
        if n == 1:
            return True

        seen = [[False] * 8 for _ in range(8)]
        stack = [pieces[0]]
        seen[pieces[0][0]][pieces[0][1]] = True
        reached = 0

        while stack:
            r, c = stack.pop()
            reached += 1
            for dr, dc in DIRS:
                rr = r + dr
                cc = c + dc
                if inside(rr, cc) and not seen[rr][cc] and B[rr][cc] == side:
                    seen[rr][cc] = True
                    stack.append((rr, cc))

        return reached == n

    def terminal_value(depth):
        n1 = count_pieces(1)
        n2 = count_pieces(-1)

        if n1 == 0:
            return -WIN - depth
        if n2 == 0:
            return WIN + depth

        c1 = is_connected(1)
        c2 = is_connected(-1)

        if c1 and not c2:
            return WIN + depth
        if c2 and not c1:
            return -WIN - depth
        if c1 and c2:
            return 0

        return None

    def value_after_move(mover, depth):
        opponent = -mover

        if count_pieces(opponent) == 0:
            return WIN + depth if mover == 1 else -WIN - depth

        if is_connected(mover):
            return WIN + depth if mover == 1 else -WIN - depth

        if count_pieces(mover) == 0:
            return -WIN - depth if mover == 1 else WIN + depth

        if is_connected(opponent):
            return -WIN - depth if mover == 1 else WIN + depth

        return None

    def stats(side):
        pieces = []
        for r in range(8):
            for c in range(8):
                if B[r][c] == side:
                    pieces.append((r, c))

        n = len(pieces)
        if n == 0:
            return 8, 0.0, 8.0, 8.0, 0.0, 64.0, 0
        if n == 1:
            r, c = pieces[0]
            center = abs(r - 3.5) + abs(c - 3.5)
            return 1, 1.0, 0.0, center, 0.0, 1.0, 1

        visited = [[False] * 8 for _ in range(8)]
        comps = 0
        largest = 0

        for sr, sc in pieces:
            if visited[sr][sc]:
                continue
            comps += 1
            size = 0
            stack = [(sr, sc)]
            visited[sr][sc] = True

            while stack:
                r, c = stack.pop()
                size += 1
                for dr, dc in DIRS:
                    rr = r + dr
                    cc = c + dc
                    if inside(rr, cc) and not visited[rr][cc] and B[rr][cc] == side:
                        visited[rr][cc] = True
                        stack.append((rr, cc))

            if size > largest:
                largest = size

        pair_sum = 0
        pair_count = 0
        for i in range(n):
            r1, c1 = pieces[i]
            for j in range(i + 1, n):
                r2, c2 = pieces[j]
                pair_sum += max(abs(r1 - r2), abs(c1 - c2))
                pair_count += 1

        avg_pair = pair_sum / pair_count if pair_count else 0.0

        center_sum = 0.0
        min_r = min_c = 8
        max_r = max_c = -1
        for r, c in pieces:
            center_sum += abs(r - 3.5) + abs(c - 3.5)
            if r < min_r:
                min_r = r
            if r > max_r:
                max_r = r
            if c < min_c:
                min_c = c
            if c > max_c:
                max_c = c

        center = center_sum / n
        area = float((max_r - min_r + 1) * (max_c - min_c + 1))

        links = 0
        half_dirs = [(1, 0), (0, 1), (1, 1), (1, -1)]
        for r, c in pieces:
            for dr, dc in half_dirs:
                rr = r + dr
                cc = c + dc
                if inside(rr, cc) and B[rr][cc] == side:
                    links += 1

        adj = links / n

        return comps, largest / n, avg_pair, center, adj, area, n

    def evaluate():
        tv = terminal_value(0)
        if tv is not None:
            return tv

        c1, f1, d1, cen1, adj1, area1, n1 = stats(1)
        c2, f2, d2, cen2, adj2, area2, n2 = stats(-1)

        score = 0.0
        score += 900.0 * (c2 - c1)
        score += 350.0 * (f1 - f2)
        score += 45.0 * (d2 - d1)
        score += 12.0 * (cen2 - cen1)
        score += 80.0 * (adj1 - adj2)
        score += 6.0 * (area2 - area1)
        score += 4.0 * (n1 - n2)

        return score

    def move_score(m, side):
        fr, fc, tr, tc, cap = m
        capture = 1 if cap == -side else 0

        friendly_neighbors = 0
        for dr, dc in DIRS:
            rr = tr + dr
            cc = tc + dc
            if inside(rr, cc) and B[rr][cc] == side:
                friendly_neighbors += 1

        center_dist = abs(tr - 3.5) + abs(tc - 3.5)
        local = 100.0 * capture + 12.0 * friendly_neighbors - 3.0 * center_dist

        return local if side == 1 else -local

    def ordered_moves(side):
        moves = generate_moves(side)
        moves.sort(key=lambda m: move_score(m, side), reverse=(side == 1))
        return moves

    def alphabeta(depth, side, alpha, beta):
        nonlocal nodes

        nodes += 1
        if (nodes & 255) == 0 and time.time() > end_time:
            raise Timeout()

        tv = terminal_value(depth)
        if tv is not None:
            return tv

        if depth <= 0:
            return evaluate()

        moves = ordered_moves(side)
        if not moves:
            return evaluate()

        if side == 1:
            value = -INF

            for m in moves:
                make_move(m, side)
                try:
                    immediate = value_after_move(side, depth)
                    if immediate is not None:
                        child = immediate
                    else:
                        child = alphabeta(depth - 1, -side, alpha, beta)
                finally:
                    undo_move(m, side)

                if child > value:
                    value = child
                if value > alpha:
                    alpha = value
                if alpha >= beta:
                    break

            return value

        else:
            value = INF

            for m in moves:
                make_move(m, side)
                try:
                    immediate = value_after_move(side, depth)
                    if immediate is not None:
                        child = immediate
                    else:
                        child = alphabeta(depth - 1, -side, alpha, beta)
                finally:
                    undo_move(m, side)

                if child < value:
                    value = child
                if value < beta:
                    beta = value
                if alpha >= beta:
                    break

            return value

    root_moves = generate_moves(1)

    if not root_moves:
        return "0,0:0,0"

    root_moves.sort(key=lambda m: move_score(m, 1), reverse=True)
    best_move = root_moves[0]

    for m in root_moves:
        make_move(m, 1)
        try:
            immediate = value_after_move(1, 100)
            if immediate is not None and immediate > 0:
                fr, fc, tr, tc, _ = m
                return f"{fr},{fc}:{tr},{tc}"
        finally:
            undo_move(m, 1)

    max_depth = 5

    for depth in range(1, max_depth + 1):
        if time.time() > end_time:
            break

        try:
            if best_move in root_moves:
                ordered_root = [best_move] + [m for m in root_moves if m != best_move]
            else:
                ordered_root = list(root_moves)

            local_best = best_move
            local_score = -INF
            alpha = -INF
            beta = INF

            for m in ordered_root:
                if time.time() > end_time:
                    raise Timeout()

                make_move(m, 1)
                try:
                    immediate = value_after_move(1, depth)
                    if immediate is not None:
                        score = immediate
                    else:
                        score = alphabeta(depth - 1, -1, alpha, beta)
                finally:
                    undo_move(m, 1)

                if score > local_score:
                    local_score = score
                    local_best = m

                if local_score > alpha:
                    alpha = local_score

            best_move = local_best

        except Timeout:
            break

    fr, fc, tr, tc, _ = best_move
    return f"{fr},{fc}:{tr},{tc}"
