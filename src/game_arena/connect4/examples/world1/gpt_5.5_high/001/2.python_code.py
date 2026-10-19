
import time

ROWS = 6
COLS = 7
STRIDE = 7

ORDER = (3, 4, 2, 5, 1, 6, 0)

BOTTOM_MASKS = tuple(1 << (c * STRIDE) for c in range(COLS))
TOP_MASKS = tuple(1 << (c * STRIDE + ROWS - 1) for c in range(COLS))
COL_MASKS = tuple(((1 << ROWS) - 1) << (c * STRIDE) for c in range(COLS))
BOARD_MASK = 0
for _m in COL_MASKS:
    BOARD_MASK |= _m

COL_WEIGHTS = (3, 4, 5, 7, 5, 4, 3)

INF = 10 ** 9
WIN = 1_000_000
TIME_LIMIT = 0.90


def _make_windows():
    windows = []
    directions = ((1, 0), (0, 1), (1, 1), (1, -1))
    for dc, dr in directions:
        for c in range(COLS):
            for r in range(ROWS):
                c2 = c + 3 * dc
                r2 = r + 3 * dr
                if 0 <= c2 < COLS and 0 <= r2 < ROWS:
                    mask = 0
                    for k in range(4):
                        cc = c + k * dc
                        rr = r + k * dr
                        mask |= 1 << (cc * STRIDE + rr)
                    windows.append(mask)
    return tuple(windows)


WINDOWS = _make_windows()

_DEADLINE = 0.0
_NODES = 0
_TT = {}
_BEST = {}


class _SearchTimeout(Exception):
    pass


def _touch():
    global _NODES
    _NODES += 1
    if (_NODES & 255) == 0 and time.perf_counter() > _DEADLINE:
        raise _SearchTimeout()


def _has_won(p):
    m = p & (p >> 1)
    if m & (m >> 2):
        return True
    m = p & (p >> STRIDE)
    if m & (m >> (2 * STRIDE)):
        return True
    m = p & (p >> (STRIDE - 1))
    if m & (m >> (2 * (STRIDE - 1))):
        return True
    m = p & (p >> (STRIDE + 1))
    if m & (m >> (2 * (STRIDE + 1))):
        return True
    return False


def _build_position(board):
    me = 0
    opp = 0
    for rt in range(ROWS):
        row = board[rt]
        r = ROWS - 1 - rt
        for c in range(COLS):
            v = row[c]
            if v == 1:
                me |= 1 << (c * STRIDE + r)
            elif v == -1:
                opp |= 1 << (c * STRIDE + r)
    return me, opp


def _legal_bits(mask):
    res = []
    for c in ORDER:
        bit = (mask + BOTTOM_MASKS[c]) & COL_MASKS[c]
        if bit:
            res.append((c, bit))
    return res


def _is_legal_col(mask, col):
    return 0 <= col < COLS and (mask & TOP_MASKS[col]) == 0


def _with_hint_first(legal, hint):
    if hint is None or hint < 0:
        return legal
    for i, pair in enumerate(legal):
        if pair[0] == hint:
            if i == 0:
                return legal
            return [pair] + legal[:i] + legal[i + 1:]
    return legal


def _evaluate(pos, opp, legal=None):
    mask = pos | opp
    if legal is None:
        legal = _legal_bits(mask)

    score = 0

    for c in range(COLS):
        score += COL_WEIGHTS[c] * 4 * (
            (pos & COL_MASKS[c]).bit_count()
            - (opp & COL_MASKS[c]).bit_count()
        )

    playable = 0
    own_now = 0
    opp_now = 0

    for _, bit in legal:
        playable |= bit
        if _has_won(pos | bit):
            own_now += 1
        if _has_won(opp | bit):
            opp_now += 1

    if own_now:
        return 500_000 + 10_000 * own_now + score
    if opp_now > 1:
        return -500_000 - 10_000 * opp_now + score
    if opp_now == 1:
        score -= 900

    for w in WINDOWS:
        a = (pos & w).bit_count()
        b = (opp & w).bit_count()

        if a and b:
            continue

        empty = w & ~mask

        if a:
            if a == 4:
                return WIN
            if a == 3:
                score += 180 if (empty & playable) else 70
            elif a == 2:
                score += 22
            elif a == 1:
                score += 3
        elif b:
            if b == 4:
                return -WIN
            if b == 3:
                score -= 220 if (empty & playable) else 85
            elif b == 2:
                score -= 26
            elif b == 1:
                score -= 3

    return score


def _negamax(pos, opp, depth, alpha, beta):
    _touch()

    mask = pos | opp
    if mask == BOARD_MASK:
        return 0

    key = (pos, opp, depth)
    alpha_start = alpha
    beta_start = beta

    entry = _TT.get(key)
    if entry is not None:
        flag, val, _ = entry
        if flag == 0:
            return val
        if flag == 1:
            if val > alpha:
                alpha = val
        elif flag == 2:
            if val < beta:
                beta = val
        if alpha >= beta:
            return val

    legal = _legal_bits(mask)
    if not legal:
        return 0

    for c, bit in legal:
        if _has_won(pos | bit):
            val = WIN + depth
            _TT[key] = (0, val, c)
            _BEST[(pos, opp)] = c
            return val

    opp_threat_count = 0
    forced = None
    for c, bit in legal:
        if _has_won(opp | bit):
            opp_threat_count += 1
            forced = (c, bit)
            if opp_threat_count > 1:
                val = -WIN - depth
                _TT[key] = (0, val, c)
                return val

    if depth <= 0:
        val = _evaluate(pos, opp, legal)
        _TT[key] = (0, val, None)
        return val

    if forced is not None:
        moves = [forced]
    else:
        moves = _with_hint_first(legal, _BEST.get((pos, opp), -1))

    best_val = -INF
    best_move = moves[0][0]

    for c, bit in moves:
        score = -_negamax(opp, pos | bit, depth - 1, -beta, -alpha)

        if score > best_val:
            best_val = score
            best_move = c

        if score > alpha:
            alpha = score

        if alpha >= beta:
            break

    if best_val <= alpha_start:
        flag = 2
    elif best_val >= beta_start:
        flag = 1
    else:
        flag = 0

    _TT[key] = (flag, best_val, best_move)
    _BEST[(pos, opp)] = best_move
    return best_val


def _root_search(pos, opp, depth, fallback):
    mask = pos | opp
    legal = _legal_bits(mask)

    opp_threats = []
    for c, bit in legal:
        if _has_won(opp | bit):
            opp_threats.append((c, bit))

    if len(opp_threats) == 1:
        moves = opp_threats
    else:
        hint = _BEST.get((pos, opp), fallback)
        moves = _with_hint_first(legal, hint)

    alpha = -INF
    beta = INF
    best_score = -INF
    best_move = fallback

    for c, bit in moves:
        if _has_won(pos | bit):
            score = WIN + depth
        else:
            score = -_negamax(opp, pos | bit, depth - 1, -beta, -alpha)

        if score > best_score:
            best_score = score
            best_move = c

        if score > alpha:
            alpha = score

    _BEST[(pos, opp)] = best_move
    return best_score, best_move


def policy(board: list[list[int]]) -> int:
    global _DEADLINE, _NODES, _TT, _BEST

    pos, opp = _build_position(board)
    mask = pos | opp
    legal = _legal_bits(mask)

    if not legal:
        return 0

    fallback = legal[0][0]

    for c, bit in legal:
        if _has_won(pos | bit):
            return int(c)

    opp_threats = []
    for c, bit in legal:
        if _has_won(opp | bit):
            opp_threats.append(c)

    if opp_threats:
        return int(opp_threats[0])

    if mask == 0 and _is_legal_col(mask, 3):
        return 3

    _TT = {}
    _BEST = {}
    _NODES = 0
    _DEADLINE = time.perf_counter() + TIME_LIMIT

    best = fallback
    empties = ROWS * COLS - mask.bit_count()
    max_depth = empties if empties <= 24 else 18

    for depth in range(1, max_depth + 1):
        try:
            score, move = _root_search(pos, opp, depth, best)
            if _is_legal_col(mask, move):
                best = move

            if score >= WIN:
                break

            if time.perf_counter() > _DEADLINE:
                break

        except _SearchTimeout:
            break

    if _is_legal_col(mask, best):
        return int(best)

    for c, _ in legal:
        if _is_legal_col(mask, c):
            return int(c)

    return 0
