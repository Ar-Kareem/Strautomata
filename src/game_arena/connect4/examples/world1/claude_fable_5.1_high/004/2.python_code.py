
import time

WIDTH, HEIGHT = 7, 6
H1 = HEIGHT + 1
BOTTOM = sum(1 << (c * H1) for c in range(WIDTH))
BOARD_MASK = BOTTOM * ((1 << HEIGHT) - 1)
COL_MASK = [((1 << HEIGHT) - 1) << (c * H1) for c in range(WIDTH)]
CENTER = COL_MASK[3]
ORDER = [3, 2, 4, 1, 5, 0, 6]
WIN = 100000
WEIGHTS = [0, 1, 5, 25]
TIME_LIMIT = 0.70

try:
    (1).bit_count()
    def popcount(x):
        return x.bit_count()
except Exception:
    def popcount(x):
        return bin(x).count("1")


def _gen_windows():
    wins = []
    for c in range(WIDTH):
        for r in range(HEIGHT):
            for dc, dr in ((0, 1), (1, 0), (1, 1), (1, -1)):
                ec, er = c + 3 * dc, r + 3 * dr
                if 0 <= ec < WIDTH and 0 <= er < HEIGHT:
                    m = 0
                    for i in range(4):
                        m |= 1 << ((c + i * dc) * H1 + (r + i * dr))
                    wins.append(m)
    return wins


WINDOWS = _gen_windows()


def winning_positions(pos, mask):
    r = (pos << 1) & (pos << 2) & (pos << 3)
    # horizontal
    p = (pos << 7) & (pos << 14)
    r |= p & (pos << 21)
    r |= p & (pos >> 7)
    p = (pos >> 7) & (pos >> 14)
    r |= p & (pos << 7)
    r |= p & (pos >> 21)
    # diagonal (shift 6)
    p = (pos << 6) & (pos << 12)
    r |= p & (pos << 18)
    r |= p & (pos >> 6)
    p = (pos >> 6) & (pos >> 12)
    r |= p & (pos << 6)
    r |= p & (pos >> 18)
    # diagonal (shift 8)
    p = (pos << 8) & (pos << 16)
    r |= p & (pos << 24)
    r |= p & (pos >> 8)
    p = (pos >> 8) & (pos >> 16)
    r |= p & (pos << 8)
    r |= p & (pos >> 24)
    return r & (BOARD_MASK ^ mask)


def evaluate(mine, opp):
    s = 0
    for w in WINDOWS:
        if not (w & opp):
            m = w & mine
            if m:
                s += WEIGHTS[popcount(m)]
        elif not (w & mine):
            s -= WEIGHTS[popcount(w & opp)]
    s += 2 * (popcount(mine & CENTER) - popcount(opp & CENTER))
    return s


class Searcher:
    def __init__(self, deadline):
        self.deadline = deadline
        self.nodes = 0
        self.tt = {}

    def negamax(self, mine, opp, depth, alpha, beta):
        self.nodes += 1
        if (self.nodes & 511) == 0 and time.perf_counter() > self.deadline:
            raise TimeoutError
        mask = mine | opp
        possible = (mask + BOTTOM) & BOARD_MASK
        if winning_positions(mine, mask) & possible:
            return WIN + depth
        if possible == 0:
            return 0
        if depth == 0:
            return evaluate(mine, opp)

        opp_cells = winning_positions(opp, mask)
        opp_win = opp_cells & possible
        if opp_win:
            if opp_win & (opp_win - 1):
                return -(WIN + depth - 1)
            moves = opp_win
        else:
            moves = possible & ~(opp_cells >> 1)
            if moves == 0:
                return -(WIN + depth - 2)

        key = (mine, mask)
        entry = self.tt.get(key)
        tt_move = -1
        orig_alpha = alpha
        if entry is not None:
            d, v, flag, bm = entry
            tt_move = bm
            if d >= depth:
                if flag == 0:
                    return v
                elif flag == 1:
                    if v > alpha:
                        alpha = v
                else:
                    if v < beta:
                        beta = v
                if alpha >= beta:
                    return v

        best = -10 * WIN
        best_move = -1
        order = ORDER
        if tt_move >= 0:
            order = [tt_move] + [c for c in ORDER if c != tt_move]
        for c in order:
            m = moves & COL_MASK[c]
            if not m:
                continue
            v = -self.negamax(opp, mine | m, depth - 1, -beta, -alpha)
            if v > best:
                best = v
                best_move = c
            if v > alpha:
                alpha = v
                if alpha >= beta:
                    break

        if best <= orig_alpha:
            flag = 2
        elif best >= beta:
            flag = 1
        else:
            flag = 0
        self.tt[key] = (depth, best, flag, best_move)
        return best

    def root(self, mine, opp, depth, first):
        mask = mine | opp
        possible = (mask + BOTTOM) & BOARD_MASK
        my_win = winning_positions(mine, mask) & possible
        if my_win:
            for c in ORDER:
                if my_win & COL_MASK[c]:
                    return WIN + depth, c
        opp_cells = winning_positions(opp, mask)
        opp_win = opp_cells & possible
        if opp_win:
            moves = opp_win
        else:
            moves = possible & ~(opp_cells >> 1)
            if moves == 0:
                moves = possible
        order = ORDER
        if first is not None and first >= 0:
            order = [first] + [c for c in ORDER if c != first]
        alpha, beta = -10 * WIN, 10 * WIN
        best = -10 * WIN
        best_move = -1
        for c in order:
            m = moves & COL_MASK[c]
            if not m:
                continue
            v = -self.negamax(opp, mine | m, depth - 1, -beta, -alpha)
            if v > best:
                best = v
                best_move = c
            if v > alpha:
                alpha = v
        return best, best_move


def policy(board):
    start = time.perf_counter()
    legal = [c for c in ORDER if board[0][c] == 0]
    if not legal:
        return 3
    fallback = legal[0]
    try:
        mine = 0
        opp = 0
        count = 0
        for r in range(HEIGHT):
            row = board[r]
            for c in range(WIDTH):
                v = row[c]
                if v:
                    bit = 1 << (c * H1 + (HEIGHT - 1 - r))
                    count += 1
                    if v == 1:
                        mine |= bit
                    else:
                        opp |= bit
        if count == 0:
            return 3

        searcher = Searcher(start + TIME_LIMIT)
        best_move = fallback
        prev = None
        for depth in range(1, 43):
            try:
                val, mv = searcher.root(mine, opp, depth, prev)
            except TimeoutError:
                break
            if mv is not None and mv >= 0 and board[0][mv] == 0:
                best_move = mv
                prev = mv
            if abs(val) >= WIN - 100:
                break
            if time.perf_counter() > searcher.deadline:
                break
        if board[0][best_move] != 0:
            return fallback
        return int(best_move)
    except Exception:
        return fallback
