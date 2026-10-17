
import time

BOARD_N = 8
WIN_SCORE = 1_000_000

DIRS = [
    (-1, 0), (1, 0), (0, -1), (0, 1),
    (-1, -1), (1, 1), (-1, 1), (1, -1),
]

# Center bonus: higher near the middle.
CENTER = [
    [14 - (abs(2 * r - 7) + abs(2 * c - 7)) for c in range(8)]
    for r in range(8)
]

# Precompute 8-neighbors for each square.
NEIGHBORS = [[[] for _ in range(8)] for _ in range(8)]
for r in range(8):
    for c in range(8):
        lst = []
        for dr, dc in DIRS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < 8 and 0 <= cc < 8:
                lst.append((rr, cc))
        NEIGHBORS[r][c] = lst


class LOAAgent:
    def __init__(self):
        self.deadline = 0.0
        self.tt = {}
        self.node_counter = 0

    def check_time(self):
        self.node_counter += 1
        if (self.node_counter & 1023) == 0 and time.perf_counter() >= self.deadline:
            raise TimeoutError

    def board_key(self, board):
        return bytes(cell + 1 for row in board for cell in row)

    def is_connected(self, board, player):
        start = None
        total = 0
        for r in range(8):
            row = board[r]
            for c in range(8):
                if row[c] == player:
                    total += 1
                    if start is None:
                        start = (r, c)
        if total <= 1:
            return True

        seen = [[False] * 8 for _ in range(8)]
        stack = [start]
        seen[start[0]][start[1]] = True
        reached = 1

        while stack:
            r, c = stack.pop()
            for rr, cc in NEIGHBORS[r][c]:
                if not seen[rr][cc] and board[rr][cc] == player:
                    seen[rr][cc] = True
                    reached += 1
                    if reached == total:
                        return True
                    stack.append((rr, cc))
        return False

    def group_features(self, board, player):
        count = 0
        cent = 0
        adj = 0
        minr = 8
        maxr = -1
        minc = 8
        maxc = -1

        for r in range(8):
            row = board[r]
            for c in range(8):
                if row[c] == player:
                    count += 1
                    cent += CENTER[r][c]
                    if r < minr:
                        minr = r
                    if r > maxr:
                        maxr = r
                    if c < minc:
                        minc = c
                    if c > maxc:
                        maxc = c
                    local = 0
                    for rr, cc in NEIGHBORS[r][c]:
                        if board[rr][cc] == player:
                            local += 1
                    adj += local

        if count == 0:
            return (0, 0, 0, 0, 0, 0)

        # Connected components and largest component.
        seen = [[False] * 8 for _ in range(8)]
        comps = 0
        largest = 0
        for r in range(8):
            for c in range(8):
                if board[r][c] == player and not seen[r][c]:
                    comps += 1
                    size = 0
                    stack = [(r, c)]
                    seen[r][c] = True
                    while stack:
                        x, y = stack.pop()
                        size += 1
                        for xx, yy in NEIGHBORS[x][y]:
                            if board[xx][yy] == player and not seen[xx][yy]:
                                seen[xx][yy] = True
                                stack.append((xx, yy))
                    if size > largest:
                        largest = size

        span = (maxr - minr) + (maxc - minc)
        cent_avg = (10 * cent) // count
        adj_avg = (10 * adj) // count
        return (count, comps, largest, span, cent_avg, adj_avg)

    def evaluate(self, board):
        my_n, my_comp, my_largest, my_span, my_cent, my_adj = self.group_features(board, 1)
        op_n, op_comp, op_largest, op_span, op_cent, op_adj = self.group_features(board, -1)

        score = 0
        score += 210 * (op_comp - my_comp)
        score += 30 * (my_largest - op_largest)
        score += 4 * (my_adj - op_adj)
        score += 3 * (my_cent - op_cent)
        score += -14 * (my_span - op_span)
        score += 2 * (op_n - my_n)  # slightly prefer having fewer pieces to connect
        return score

    def generate_moves(self, board):
        row_count = [0] * 8
        col_count = [0] * 8
        diag_count = [0] * 15      # r-c+7
        adiag_count = [0] * 15     # r+c

        for r in range(8):
            row = board[r]
            for c in range(8):
                if row[c] != 0:
                    row_count[r] += 1
                    col_count[c] += 1
                    diag_count[r - c + 7] += 1
                    adiag_count[r + c] += 1

        moves = []
        for r in range(8):
            row = board[r]
            for c in range(8):
                if row[c] != 1:
                    continue

                for dr, dc in DIRS:
                    if dr == 0:
                        dist = row_count[r]
                    elif dc == 0:
                        dist = col_count[c]
                    elif dr == dc:
                        dist = diag_count[r - c + 7]
                    else:
                        dist = adiag_count[r + c]

                    tr = r + dr * dist
                    tc = c + dc * dist
                    if not (0 <= tr < 8 and 0 <= tc < 8):
                        continue
                    if board[tr][tc] == 1:
                        continue

                    rr = r + dr
                    cc = c + dc
                    legal = True
                    for _ in range(dist - 1):
                        if board[rr][cc] == -1:
                            legal = False
                            break
                        rr += dr
                        cc += dc

                    if legal:
                        moves.append((r, c, tr, tc))
        return moves

    def apply_move(self, board, move):
        fr, fc, tr, tc = move
        # Return board from next player's perspective:
        # negate all values, then place moved piece as opponent (-1).
        nb = [[-cell for cell in row] for row in board]
        nb[fr][fc] = 0
        nb[tr][tc] = -1
        return nb

    def immediate_outcome_after_move(self, child_board):
        # child_board is from next player's perspective.
        # The mover's pieces are now -1.
        if self.is_connected(child_board, -1):
            return WIN_SCORE
        if self.is_connected(child_board, 1):
            return -WIN_SCORE
        return None

    def move_order_score(self, board, move):
        fr, fc, tr, tc = move
        score = 0

        if board[tr][tc] == -1:
            score += 40

        score += CENTER[tr][tc] - CENTER[fr][fc]

        src_neighbors = 0
        dst_neighbors = 0
        for rr, cc in NEIGHBORS[fr][fc]:
            if board[rr][cc] == 1 and not (rr == tr and cc == tc):
                src_neighbors += 1
        for rr, cc in NEIGHBORS[tr][tc]:
            if board[rr][cc] == 1 and not (rr == fr and cc == fc):
                dst_neighbors += 1

        score += 6 * (dst_neighbors - src_neighbors)
        return score

    def negamax(self, board, depth, alpha, beta):
        self.check_time()

        key = self.board_key(board)
        entry = self.tt.get(key)
        if entry is not None and entry[0] >= depth:
            return entry[1]

        if self.is_connected(board, 1):
            return WIN_SCORE
        if self.is_connected(board, -1):
            return -WIN_SCORE

        if depth == 0:
            return self.evaluate(board)

        moves = self.generate_moves(board)
        if not moves:
            return -WIN_SCORE

        tt_move = entry[2] if entry is not None and len(entry) > 2 else None
        moves.sort(
            key=lambda m: (1 if m == tt_move else 0, self.move_order_score(board, m)),
            reverse=True,
        )

        best_score = -10**18
        best_move = moves[0]

        for mv in moves:
            child = self.apply_move(board, mv)
            outcome = self.immediate_outcome_after_move(child)
            if outcome is None:
                score = -self.negamax(child, depth - 1, -beta, -alpha)
            else:
                score = outcome

            if score > best_score:
                best_score = score
                best_move = mv

            if best_score > alpha:
                alpha = best_score
            if alpha >= beta:
                break

        self.tt[key] = (depth, best_score, best_move)
        return best_score

    def root_search(self, board, moves, depth):
        entry = self.tt.get(self.board_key(board))
        tt_move = entry[2] if entry is not None and len(entry) > 2 else None

        ordered = sorted(
            moves,
            key=lambda m: (1 if m == tt_move else 0, self.move_order_score(board, m)),
            reverse=True,
        )

        best_move = ordered[0]
        best_score = -10**18
        alpha = -10**18
        beta = 10**18

        for mv in ordered:
            self.check_time()
            child = self.apply_move(board, mv)
            outcome = self.immediate_outcome_after_move(child)
            if outcome is None:
                score = -self.negamax(child, depth - 1, -beta, -alpha)
            else:
                score = outcome

            if score > best_score:
                best_score = score
                best_move = mv

            if best_score > alpha:
                alpha = best_score

        self.tt[self.board_key(board)] = (depth, best_score, best_move)
        return best_move, best_score

    def opponent_has_immediate_win(self, child_board):
        self.check_time()
        opp_moves = self.generate_moves(child_board)
        for mv in opp_moves:
            gc = self.apply_move(child_board, mv)
            if self.is_connected(gc, -1):
                return True
        return False

    def choose_move(self, board):
        legal_moves = self.generate_moves(board)
        if not legal_moves:
            # Should not happen in normal play, but keep a syntactically valid string if ever called.
            return "0,0:0,0"

        if len(legal_moves) == 1:
            fr, fc, tr, tc = legal_moves[0]
            return f"{fr},{fc}:{tr},{tc}"

        ordered = sorted(legal_moves, key=lambda m: self.move_order_score(board, m), reverse=True)

        # Immediate winning move?
        children = []
        for mv in ordered:
            child = self.apply_move(board, mv)
            if self.is_connected(child, -1):
                fr, fc, tr, tc = mv
                return f"{fr},{fc}:{tr},{tc}"
            children.append((mv, child))

        # Tactical filter: avoid moves that let opponent win immediately if possible.
        safe_moves = []
        risky_moves = []

        try:
            for mv, child in children:
                if self.is_connected(child, 1):
                    risky_moves.append(mv)
                    continue
                if self.opponent_has_immediate_win(child):
                    risky_moves.append(mv)
                else:
                    safe_moves.append(mv)
        except TimeoutError:
            safe_moves = []

        root_moves = safe_moves if safe_moves else ordered
        best_move = root_moves[0]

        # Iterative deepening.
        max_depth = 5 if len(root_moves) <= 18 else 4
        for depth in range(1, max_depth + 1):
            try:
                mv, score = self.root_search(board, root_moves, depth)
                best_move = mv
                if abs(score) >= WIN_SCORE:
                    break
            except TimeoutError:
                break

        fr, fc, tr, tc = best_move
        return f"{fr},{fc}:{tr},{tc}"


def policy(board) -> str:
    agent = LOAAgent()
    agent.deadline = time.perf_counter() + 0.93
    return agent.choose_move(board)
