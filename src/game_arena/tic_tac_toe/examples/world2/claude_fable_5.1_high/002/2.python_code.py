
import time

# Precompute winning lines (4 rows, 4 cols, 2 diagonals) on a flat 16-cell board
LINES = []
for r in range(4):
    LINES.append([r * 4 + c for c in range(4)])
for c in range(4):
    LINES.append([r * 4 + c for r in range(4)])
LINES.append([0, 5, 10, 15])
LINES.append([3, 6, 9, 12])

CELL_LINES = [[] for _ in range(16)]
for li, line in enumerate(LINES):
    for cell in line:
        CELL_LINES[cell].append(li)

# Static ordering: cells on more lines first
STATIC_ORDER = sorted(range(16), key=lambda i: -len(CELL_LINES[i]))

WEIGHTS = [0, 1, 10, 100]
WIN_SCORE = 100000
TIME_LIMIT = 0.75


class Timeout(Exception):
    pass


def wins_with(flat, move, player):
    """Does placing `player` at `move` complete a line?"""
    for li in CELL_LINES[move]:
        ok = True
        for cell in LINES[li]:
            if cell != move and flat[cell] != player:
                ok = False
                break
        if ok:
            return True
    return False


def evaluate(flat, player):
    """Heuristic evaluation from perspective of `player`."""
    score = 0
    for line in LINES:
        mine = 0
        theirs = 0
        for cell in line:
            v = flat[cell]
            if v == player:
                mine += 1
            elif v == -player:
                theirs += 1
        if mine and theirs:
            continue
        if mine:
            score += WEIGHTS[mine]
        elif theirs:
            score -= WEIGHTS[theirs]
    return score


class Searcher:
    def __init__(self, deadline):
        self.deadline = deadline
        self.nodes = 0
        self.tt = {}

    def check_time(self):
        self.nodes += 1
        if (self.nodes & 1023) == 0:
            if time.time() > self.deadline:
                raise Timeout()

    def negamax(self, flat, player, depth, alpha, beta, empties_count):
        self.check_time()
        if empties_count == 0:
            return 0
        if depth == 0:
            return evaluate(flat, player)

        key = (tuple(flat), player)
        entry = self.tt.get(key)
        if entry is not None:
            e_depth, e_flag, e_val = entry
            if e_depth >= depth:
                if e_flag == 0:
                    return e_val
                elif e_flag == 1 and e_val > alpha:
                    alpha = e_val
                elif e_flag == 2 and e_val < beta:
                    beta = e_val
                if alpha >= beta:
                    return e_val

        orig_alpha = alpha
        best = -10 ** 9
        for m in STATIC_ORDER:
            if flat[m] != 0:
                continue
            if wins_with(flat, m, player):
                val = WIN_SCORE + depth
            else:
                flat[m] = player
                val = -self.negamax(flat, -player, depth - 1, -beta, -alpha, empties_count - 1)
                flat[m] = 0
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

        if best <= orig_alpha:
            flag = 2  # upper bound
        elif best >= beta:
            flag = 1  # lower bound
        else:
            flag = 0  # exact
        self.tt[key] = (depth, flag, best)
        return best


def policy(board):
    try:
        start = time.time()
        flat = [board[r][c] for r in range(4) for c in range(4)]
        empties = [i for i in range(16) if flat[i] == 0]
        if not empties:
            return (0, 0)
        if len(empties) == 16:
            return (1, 1)

        # Immediate win
        for m in empties:
            if wins_with(flat, m, 1):
                return divmod(m, 4)
        # Immediate block
        blocks = [m for m in empties if wins_with(flat, m, -1)]
        if blocks:
            return divmod(blocks[0], 4)

        deadline = start + TIME_LIMIT
        searcher = Searcher(deadline)

        ordered = [m for m in STATIC_ORDER if flat[m] == 0]
        best_move = ordered[0]
        max_depth = len(empties)

        depth = 1
        while depth <= max_depth:
            try:
                alpha = -10 ** 9
                beta = 10 ** 9
                cur_best = None
                cur_best_val = -10 ** 9
                # Search previous best first
                moves = [best_move] + [m for m in ordered if m != best_move]
                for m in moves:
                    flat[m] = 1
                    val = -searcher.negamax(flat, -1, depth - 1, -beta, -alpha, len(empties) - 1)
                    flat[m] = 0
                    if val > cur_best_val:
                        cur_best_val = val
                        cur_best = m
                    if val > alpha:
                        alpha = val
                if cur_best is not None:
                    best_move = cur_best
                if cur_best_val >= WIN_SCORE or cur_best_val <= -WIN_SCORE:
                    break
                depth += 1
            except Timeout:
                break

        if flat[best_move] != 0:
            best_move = empties[0]
        return divmod(best_move, 4)
    except Exception:
        for r in range(4):
            for c in range(4):
                if board[r][c] == 0:
                    return (r, c)
        return (0, 0)
