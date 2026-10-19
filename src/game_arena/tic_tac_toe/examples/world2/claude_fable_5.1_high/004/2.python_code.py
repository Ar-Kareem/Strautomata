
import time

# ---------- Precomputation ----------
LINES = []
for r in range(4):
    LINES.append(sum(1 << (r * 4 + c) for c in range(4)))
for c in range(4):
    LINES.append(sum(1 << (r * 4 + c) for r in range(4)))
LINES.append(sum(1 << (i * 4 + i) for i in range(4)))
LINES.append(sum(1 << (i * 4 + (3 - i)) for i in range(4)))

FULL = 0xFFFF

def _is_win(m):
    for L in LINES:
        if (m & L) == L:
            return True
    return False

WIN = [_is_win(m) for m in range(1 << 16)]
POP = [bin(m).count('1') for m in range(1 << 16)]

# cell ordering: corners and centers (3 lines each) before edges (2 lines)
_cell_lines = [0] * 16
for i in range(16):
    _cell_lines[i] = sum(1 for L in LINES if (L >> i) & 1)
ORDER = sorted(range(16), key=lambda i: (-_cell_lines[i], abs(i // 4 - 1.5) + abs(i % 4 - 1.5)))

W = [0, 1, 10, 100, 0]
WIN_SCORE = 100000

class _Timeout(Exception):
    pass

_deadline = 0.0
_nodes = 0
_TT = {}

def _evaluate(me, opp):
    score = 0
    for L in LINES:
        a = me & L
        b = opp & L
        if a:
            if not b:
                score += W[POP[a]]
        elif b:
            score -= W[POP[b]]
    return score

def _negamax(me, opp, depth, alpha, beta):
    global _nodes
    _nodes += 1
    if (_nodes & 1023) == 0 and time.time() > _deadline:
        raise _Timeout()

    if WIN[opp]:
        return -(WIN_SCORE + depth)
    empty = FULL & ~(me | opp)
    if not empty:
        return 0
    if depth <= 0:
        return _evaluate(me, opp)

    key = (me, opp)
    entry = _TT.get(key)
    tt_move = -1
    if entry is not None:
        e_depth, e_flag, e_val, e_move = entry
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

    orig_alpha = alpha
    best = -10 ** 9
    best_move = -1

    moves = []
    if tt_move >= 0 and (empty >> tt_move) & 1:
        moves.append(tt_move)
    for i in ORDER:
        if (empty >> i) & 1 and i != tt_move:
            moves.append(i)

    for mv in moves:
        bit = 1 << mv
        val = -_negamax(opp, me | bit, depth - 1, -beta, -alpha)
        if val > best:
            best = val
            best_move = mv
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    if best <= orig_alpha:
        flag = 2  # upper bound
    elif best >= beta:
        flag = 1  # lower bound
    else:
        flag = 0  # exact
    _TT[key] = (depth, flag, best, best_move)
    return best

def _root_search(me, opp, depth, moves):
    best_val = -10 ** 9
    best_move = moves[0]
    alpha = -10 ** 9
    beta = 10 ** 9
    for mv in moves:
        bit = 1 << mv
        val = -_negamax(opp, me | bit, depth - 1, -beta, -alpha)
        if val > best_val:
            best_val = val
            best_move = mv
        if val > alpha:
            alpha = val
    return best_move, best_val

def policy(board):
    global _deadline, _nodes, _TT
    start = time.time()
    _deadline = start + 0.75

    me = 0
    opp = 0
    for r in range(4):
        for c in range(4):
            v = board[r][c]
            if v == 1:
                me |= 1 << (r * 4 + c)
            elif v == -1:
                opp |= 1 << (r * 4 + c)

    empty = FULL & ~(me | opp)
    legal = [i for i in ORDER if (empty >> i) & 1]
    if not legal:
        # Should not happen; return something (still may be illegal but nothing legal exists)
        for r in range(4):
            for c in range(4):
                if board[r][c] == 0:
                    return (r, c)
        return (0, 0)

    fallback = legal[0]

    # Opening move on empty board
    if not (me | opp):
        return (1, 1)

    # Immediate win
    for mv in legal:
        if WIN[me | (1 << mv)]:
            return (mv // 4, mv % 4)

    # Forced block if opponent has immediate win(s)
    threats = [mv for mv in legal if WIN[opp | (1 << mv)]]
    if len(threats) == 1:
        mv = threats[0]
        return (mv // 4, mv % 4)
    if len(threats) > 1:
        # Lost anyway unless we can win; pick a block anyway
        mv = threats[0]
        return (mv // 4, mv % 4)

    _TT = {}
    _nodes = 0
    best_move = fallback
    moves = list(legal)
    max_depth = len(legal)

    try:
        for depth in range(1, max_depth + 1):
            mv, val = _root_search(me, opp, depth, moves)
            best_move = mv
            # move best to front for next iteration
            moves.remove(mv)
            moves.insert(0, mv)
            if val >= WIN_SCORE or val <= -WIN_SCORE:
                break
            if time.time() > _deadline:
                break
    except _Timeout:
        pass
    except Exception:
        pass

    if not ((empty >> best_move) & 1):
        best_move = fallback
    return (best_move // 4, best_move % 4)
