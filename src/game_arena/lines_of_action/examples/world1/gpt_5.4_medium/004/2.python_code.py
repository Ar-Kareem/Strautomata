
import time

DIRS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
]

WIN_SCORE = 100000
INF = 10**18


def move_to_str(m):
    return f"{m[0]},{m[1]}:{m[2]},{m[3]}"


def board_key(board):
    return tuple(cell for row in board for cell in row)


def generate_moves(board):
    row_counts = [0] * 8
    col_counts = [0] * 8
    diag1_counts = [0] * 15  # r-c+7
    diag2_counts = [0] * 15  # r+c

    for r in range(8):
        for c in range(8):
            if board[r][c] != 0:
                row_counts[r] += 1
                col_counts[c] += 1
                diag1_counts[r - c + 7] += 1
                diag2_counts[r + c] += 1

    moves = []
    for r in range(8):
        for c in range(8):
            if board[r][c] != 1:
                continue

            for dr, dc in DIRS:
                if dr == 0:
                    dist = row_counts[r]
                elif dc == 0:
                    dist = col_counts[c]
                elif dr == dc:
                    dist = diag1_counts[r - c + 7]
                else:
                    dist = diag2_counts[r + c]

                tr = r + dr * dist
                tc = c + dc * dist
                if not (0 <= tr < 8 and 0 <= tc < 8):
                    continue
                if board[tr][tc] == 1:
                    continue

                blocked = False
                rr = r + dr
                cc = c + dc
                for _ in range(dist - 1):
                    if board[rr][cc] == -1:
                        blocked = True
                        break
                    rr += dr
                    cc += dc

                if not blocked:
                    moves.append((r, c, tr, tc))
    return moves


def next_board(board, move):
    fr, fc, tr, tc = move
    nb = [[-board[r][c] for c in range(8)] for r in range(8)]
    nb[fr][fc] = 0
    nb[tr][tc] = -1
    return nb


def is_connected(board, player):
    positions = []
    for r in range(8):
        for c in range(8):
            if board[r][c] == player:
                positions.append((r, c))

    if len(positions) <= 1:
        return True

    pos_set = set(positions)
    stack = [positions[0]]
    seen = {positions[0]}
    count = 0

    while stack:
        r, c = stack.pop()
        count += 1
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            p = (nr, nc)
            if p in pos_set and p not in seen:
                seen.add(p)
                stack.append(p)

    return count == len(positions)


def analyze_player(board, player):
    positions = []
    sum_r = 0
    sum_c = 0
    min_r = 8
    max_r = -1
    min_c = 8
    max_c = -1
    edge = 0

    for r in range(8):
        for c in range(8):
            if board[r][c] == player:
                positions.append((r, c))
                sum_r += r
                sum_c += c
                if r < min_r:
                    min_r = r
                if r > max_r:
                    max_r = r
                if c < min_c:
                    min_c = c
                if c > max_c:
                    max_c = c
                if r == 0 or r == 7 or c == 0 or c == 7:
                    edge += 1

    n = len(positions)
    if n == 0:
        return (1, 0, 0, 0.0, 0, 0)
    if n == 1:
        return (1, 1, 0, 0.0, 0, edge)

    pos_set = set(positions)

    components = 0
    largest = 0
    seen = set()
    for p in positions:
        if p in seen:
            continue
        components += 1
        stack = [p]
        seen.add(p)
        size = 0
        while stack:
            r, c = stack.pop()
            size += 1
            for dr, dc in DIRS:
                q = (r + dr, c + dc)
                if q in pos_set and q not in seen:
                    seen.add(q)
                    stack.append(q)
        if size > largest:
            largest = size

    adj = 0
    for r, c in positions:
        for dr, dc in DIRS:
            if (r + dr, c + dc) in pos_set:
                adj += 1
    adj //= 2

    center_r = sum_r / n
    center_c = sum_c / n
    spread = 0.0
    for r, c in positions:
        spread += abs(r - center_r) + abs(c - center_c)

    span = (max_r - min_r) + (max_c - min_c)
    return (components, largest, adj, spread, span, edge)


def evaluate(board):
    my_comp, my_largest, my_adj, my_spread, my_span, my_edge = analyze_player(board, 1)
    op_comp, op_largest, op_adj, op_spread, op_span, op_edge = analyze_player(board, -1)

    my_score = (
        -800 * (my_comp - 1)
        + 70 * my_largest
        + 14 * my_adj
        - 10 * my_span
        - 4 * my_spread
        - 6 * my_edge
    )

    op_score = (
        -800 * (op_comp - 1)
        + 70 * op_largest
        + 14 * op_adj
        - 10 * op_span
        - 4 * op_spread
        - 6 * op_edge
    )

    return int(my_score - op_score)


def quick_score_move(board, move):
    fr, fc, tr, tc = move
    score = 0

    if board[tr][tc] == -1:
        score += 120

    friendly_neighbors = 0
    enemy_neighbors = 0
    for dr, dc in DIRS:
        nr, nc = tr + dr, tc + dc
        if 0 <= nr < 8 and 0 <= nc < 8:
            if board[nr][nc] == 1 and not (nr == fr and nc == fc):
                friendly_neighbors += 1
            elif board[nr][nc] == -1:
                enemy_neighbors += 1

    score += 18 * friendly_neighbors
    score += 4 * enemy_neighbors

    score -= abs(2 * tr - 7) + abs(2 * tc - 7)

    if tr == 0 or tr == 7 or tc == 0 or tc == 7:
        score -= 3

    return score


class SearchTimeout(Exception):
    pass


class Searcher:
    def __init__(self, deadline):
        self.deadline = deadline
        self.nodes = 0
        self.eval_cache = {}

    def check_time(self):
        self.nodes += 1
        if (self.nodes & 127) == 0 and time.perf_counter() >= self.deadline:
            raise SearchTimeout

    def terminal_value(self, board, ply):
        # Previous mover's pieces are -1 in this board representation.
        # If both sides are connected, previous mover wins, so check -1 first.
        if is_connected(board, -1):
            return -WIN_SCORE + ply
        if is_connected(board, 1):
            return WIN_SCORE - ply
        return None

    def eval_board(self, board):
        k = board_key(board)
        cached = self.eval_cache.get(k)
        if cached is not None:
            return cached
        v = evaluate(board)
        self.eval_cache[k] = v
        return v

    def ordered_moves(self, board):
        moves = generate_moves(board)
        moves.sort(key=lambda m: quick_score_move(board, m), reverse=True)
        return moves

    def negamax(self, board, depth, alpha, beta, ply):
        self.check_time()

        tv = self.terminal_value(board, ply)
        if tv is not None:
            return tv

        if depth == 0:
            return self.eval_board(board)

        moves = self.ordered_moves(board)
        if not moves:
            return -WIN_SCORE + ply

        best = -INF
        for mv in moves:
            val = -self.negamax(next_board(board, mv), depth - 1, -beta, -alpha, ply + 1)
            if val > best:
                best = val
            if val > alpha:
                alpha = val
            if alpha >= beta:
                break
        return best

    def search_root(self, board, moves, depth):
        alpha = -INF
        beta = INF
        best_score = -INF
        best_move = moves[0]
        scored = []

        for mv in moves:
            self.check_time()
            val = -self.negamax(next_board(board, mv), depth - 1, -beta, -alpha, 1)
            scored.append((val, mv))
            if val > best_score:
                best_score = val
                best_move = mv
            if val > alpha:
                alpha = val

        scored.sort(key=lambda x: x[0], reverse=True)
        ordered = [m for _, m in scored]
        return best_score, best_move, ordered


def policy(board) -> str:
    try:
        b = [[int(board[r][c]) for c in range(8)] for r in range(8)]

        moves = generate_moves(b)
        if not moves:
            return "0,0:0,0"

        moves.sort(key=lambda m: quick_score_move(b, m), reverse=True)

        for mv in moves:
            nb = next_board(b, mv)
            if is_connected(nb, -1):
                return move_to_str(mv)

        best_move = moves[0]
        if len(moves) == 1:
            return move_to_str(best_move)

        deadline = time.perf_counter() + 0.94
        searcher = Searcher(deadline)

        for depth in range(1, 7):
            try:
                score, best_move, moves = searcher.search_root(b, moves, depth)
                if abs(score) >= WIN_SCORE - 10:
                    break
            except SearchTimeout:
                break

        return move_to_str(best_move)

    except Exception:
        try:
            b = [[int(board[r][c]) for c in range(8)] for r in range(8)]
            moves = generate_moves(b)
            if moves:
                return move_to_str(moves[0])
        except Exception:
            pass
        return "0,0:0,0"
