
import time

# ---------- precomputation ----------
LINES = []
for r in range(4):
    LINES.append(sum(1 << (r * 4 + c) for c in range(4)))
for c in range(4):
    LINES.append(sum(1 << (r * 4 + c) for r in range(4)))
LINES.append(sum(1 << (i * 4 + i) for i in range(4)))
LINES.append(sum(1 << (i * 4 + 3 - i) for i in range(4)))

FULL = 0xFFFF
POP = [bin(i).count("1") for i in range(1 << 16)]
WEIGHTS = [0, 1, 8, 64, 0]

# cells on diagonals belong to 3 lines -> try them first
_ORDER_CELLS = [5, 6, 9, 10, 0, 3, 12, 15, 1, 2, 4, 7, 8, 11, 13, 14]
CELL_MASKS = [1 << i for i in _ORDER_CELLS]

TIME_LIMIT = 0.70
WIN = 10000


class _Timeout(Exception):
    pass


def _is_win(mask):
    for l in LINES:
        if mask & l == l:
            return True
    return False


def _evaluate(me, opp):
    s = 0
    for l in LINES:
        m = me & l
        o = opp & l
        if m and not o:
            s += WEIGHTS[POP[m]]
        elif o and not m:
            s -= WEIGHTS[POP[o]]
    return s


class _Searcher:
    def __init__(self, deadline):
        self.deadline = deadline
        self.tt = {}
        self.nodes = 0

    def negamax(self, me, opp, depth, alpha, beta, ply):
        self.nodes += 1
        if (self.nodes & 1023) == 0 and time.perf_counter() > self.deadline:
            raise _Timeout()

        if _is_win(opp):
            return -(WIN - ply)
        empties = FULL & ~(me | opp)
        if empties == 0:
            return 0
        if depth <= 0:
            return _evaluate(me, opp)

        key = (me, opp)
        tt_move = 0
        entry = self.tt.get(key)
        alpha0 = alpha
        if entry is not None:
            e_depth, e_val, e_flag, e_move = entry
            tt_move = e_move
            if e_depth >= depth:
                if e_flag == 0:
                    return e_val
                elif e_flag == 1:
                    if e_val > alpha:
                        alpha = e_val
                else:
                    if e_val < beta:
                        beta = e_val
                if alpha >= beta:
                    return e_val

        # immediate win check
        for cm in CELL_MASKS:
            if empties & cm and _is_win(me | cm):
                val = WIN - ply - 1
                self.tt[key] = (depth, val, 0, cm)
                return val

        moves = []
        if tt_move and (empties & tt_move):
            moves.append(tt_move)
        for cm in CELL_MASKS:
            if empties & cm and cm != tt_move:
                moves.append(cm)

        best = -10 ** 9
        best_move = 0
        for cm in moves:
            val = -self.negamax(opp, me | cm, depth - 1, -beta, -alpha, ply + 1)
            if val > best:
                best = val
                best_move = cm
            if val > alpha:
                alpha = val
            if alpha >= beta:
                break

        if best <= alpha0:
            flag = 2
        elif best >= beta:
            flag = 1
        else:
            flag = 0
        self.tt[key] = (depth, best, flag, best_move)
        return best


def _mask_to_rc(mask):
    idx = mask.bit_length() - 1
    return (idx // 4, idx % 4)


def policy(board):
    start = time.perf_counter()
    try:
        me = 0
        opp = 0
        for r in range(4):
            for c in range(4):
                v = board[r][c]
                if v == 1:
                    me |= 1 << (r * 4 + c)
                elif v == -1:
                    opp |= 1 << (r * 4 + c)
        empties = FULL & ~(me | opp)
        if empties == 0:
            return (0, 0)

        empty_list = [cm for cm in CELL_MASKS if empties & cm]

        # 1. immediate win
        for cm in empty_list:
            if _is_win(me | cm):
                return _mask_to_rc(cm)

        # 2. forced block (if exactly one threat, block; else search decides)
        blocks = [cm for cm in empty_list if _is_win(opp | cm)]
        if len(blocks) == 1:
            return _mask_to_rc(blocks[0])

        if len(empty_list) == 1:
            return _mask_to_rc(empty_list[0])

        # 3. iterative deepening alpha-beta
        deadline = start + TIME_LIMIT
        searcher = _Searcher(deadline)
        best_move = empty_list[0]
        # static fallback ordering by heuristic
        best_static = -10 ** 9
        for cm in empty_list:
            v = _evaluate(me | cm, opp)
            if v > best_static:
                best_static = v
                best_move = cm

        n_empty = len(empty_list)
        root_order = list(empty_list)
        try:
            for depth in range(1, n_empty + 1):
                alpha = -10 ** 9
                beta = 10 ** 9
                cur_best = None
                cur_val = -10 ** 9
                scored = []
                for cm in root_order:
                    val = -searcher.negamax(opp, me | cm, depth - 1, -beta, -alpha, 1)
                    scored.append((val, cm))
                    if val > cur_val:
                        cur_val = val
                        cur_best = cm
                    if val > alpha:
                        alpha = val
                if cur_best is not None:
                    best_move = cur_best
                    scored.sort(key=lambda x: -x[0])
                    root_order = [cm for _, cm in scored]
                    if cur_val >= WIN - 100 or cur_val <= -(WIN - 100):
                        break
        except _Timeout:
            pass

        r, c = _mask_to_rc(best_move)
        if board[r][c] == 0:
            return (r, c)
    except Exception:
        pass

    # ultimate fallback: any legal cell
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                return (r, c)
    return (0, 0)
