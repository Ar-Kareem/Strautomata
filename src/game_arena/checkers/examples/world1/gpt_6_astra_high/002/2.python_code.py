
import time

_FULL = (1 << 64) - 1
_NOT_A = _FULL ^ 0x0101010101010101
_NOT_H = _FULL ^ 0x8080808080808080
_CROWN = (0xFF, 0xFF << 56)
_HOME = (0xFF << 56, 0xFF)
_MATE = 30000
_INF = 32000

_ADVANCE = (0, 0, 2, 5, 9, 16, 27, 40)
_CENTER = (0, 2, 4, 5, 5, 4, 2, 0)

_WHITE_PST = tuple(
    _ADVANCE[s >> 3] + _CENTER[s & 7]
    + min(s >> 3, 7 - (s >> 3))
    for s in range(64)
)
_BLACK_PST = tuple(_WHITE_PST[s ^ 56] for s in range(64))
_MAN_PST = (_BLACK_PST, _WHITE_PST)
_KING_PST = tuple(
    2 * (min(s >> 3, 7 - (s >> 3))
         + min(s & 7, 7 - (s & 7)))
    for s in range(64)
)


def _make_pass_masks():
    tables = []
    for up in (False, True):
        table = []
        for s in range(64):
            r, c = s >> 3, s & 7
            mask = 0
            rows = range(r + 1, 8) if up else range(r)
            for rr in rows:
                distance = abs(rr - r)
                for cc in range(8):
                    if ((rr + cc - r - c) & 1) == 0:
                        if abs(cc - c) <= distance + 2:
                            mask |= 1 << (8 * rr + cc)
            table.append(mask)
        tables.append(tuple(table))
    return tuple(tables)


_PASS = _make_pass_masks()

_TT = {}
_HISTORY = [[0] * 4096 for _ in range(2)]
_RECENT = []
_LAST_TOTAL = 0


class _Timeout(Exception):
    pass


def _bits(squares):
    board = 0
    for r, c in squares:
        board |= 1 << (8 * int(r) + int(c))
    return board


def _captures(men, kings, enemy_men, enemy_kings, up):
    enemy = enemy_men | enemy_kings
    empty = _FULL ^ (men | kings | enemy)
    upward = (men | kings) if up else kings
    downward = kings if up else (men | kings)
    moves = []

    targets = (((upward & _NOT_A) << 7) & enemy & _NOT_A)
    targets = (targets << 7) & empty
    while targets:
        bit = targets & -targets
        t = bit.bit_length() - 1
        moves.append(4096 | (t << 6) | (t - 14))
        targets ^= bit

    targets = (((upward & _NOT_H) << 9) & enemy & _NOT_H)
    targets = (targets << 9) & empty
    while targets:
        bit = targets & -targets
        t = bit.bit_length() - 1
        moves.append(4096 | (t << 6) | (t - 18))
        targets ^= bit

    targets = (((downward & _NOT_A) >> 9) & enemy & _NOT_A)
    targets = (targets >> 9) & empty
    while targets:
        bit = targets & -targets
        t = bit.bit_length() - 1
        moves.append(4096 | (t << 6) | (t + 18))
        targets ^= bit

    targets = (((downward & _NOT_H) >> 7) & enemy & _NOT_H)
    targets = (targets >> 7) & empty
    while targets:
        bit = targets & -targets
        t = bit.bit_length() - 1
        moves.append(4096 | (t << 6) | (t + 14))
        targets ^= bit

    return moves


def _steps(men, kings, enemy_men, enemy_kings, up):
    empty = _FULL ^ (men | kings | enemy_men | enemy_kings)
    upward = (men | kings) if up else kings
    downward = kings if up else (men | kings)
    moves = []

    targets = ((upward & _NOT_A) << 7) & empty
    while targets:
        bit = targets & -targets
        t = bit.bit_length() - 1
        moves.append((t << 6) | (t - 7))
        targets ^= bit

    targets = ((upward & _NOT_H) << 9) & empty
    while targets:
        bit = targets & -targets
        t = bit.bit_length() - 1
        moves.append((t << 6) | (t - 9))
        targets ^= bit

    targets = ((downward & _NOT_A) >> 9) & empty
    while targets:
        bit = targets & -targets
        t = bit.bit_length() - 1
        moves.append((t << 6) | (t + 9))
        targets ^= bit

    targets = ((downward & _NOT_H) >> 7) & empty
    while targets:
        bit = targets & -targets
        t = bit.bit_length() - 1
        moves.append((t << 6) | (t + 7))
        targets ^= bit

    return moves


def _mobility(men, kings, empty, up):
    upward = (men | kings) if up else kings
    downward = kings if up else (men | kings)
    return (
        ((upward & _NOT_A) << 7)
        | ((upward & _NOT_H) << 9)
        | ((downward & _NOT_A) >> 9)
        | ((downward & _NOT_H) >> 7)
    ) & empty


def _neighbors(board):
    return (
        ((board & _NOT_A) << 7)
        | ((board & _NOT_H) << 9)
        | ((board & _NOT_A) >> 9)
        | ((board & _NOT_H) >> 7)
    )


def _pursuit(kings, targets):
    if not kings or not targets:
        return 0
    squares = []
    while targets:
        bit = targets & -targets
        s = bit.bit_length() - 1
        squares.append((s >> 3, s & 7))
        targets ^= bit

    score = 0
    while kings:
        bit = kings & -kings
        s = bit.bit_length() - 1
        r, c = s >> 3, s & 7
        distance = min(max(abs(r - rr), abs(c - cc))
                       for rr, cc in squares)
        score += 4 * (7 - distance)
        kings ^= bit
    return score


def _evaluate(men, kings, enemy_men, enemy_kings, up, ply):
    own = men | kings
    enemy = enemy_men | enemy_kings
    empty = _FULL ^ (own | enemy)

    mobility = _mobility(men, kings, empty, up)
    # This evaluator is called only after ruling out captures.
    if not mobility:
        return -_MATE + ply

    enemy_mobility = _mobility(
        enemy_men, enemy_kings, empty, not up
    )

    nm = men.bit_count()
    nk = kings.bit_count()
    ne = enemy_men.bit_count()
    nek = enemy_kings.bit_count()
    total = nm + nk + ne + nek

    king_value = 178 + max(0, 24 - total)
    material = 100 * (nm - ne) + king_value * (nk - nek)
    score = material

    material_total = 100 * (nm + ne) + king_value * (nk + nek)
    if material_total and material:
        trade = 40 * abs(material) // material_total
        score += trade if material > 0 else -trade

    own_table = _MAN_PST[up]
    enemy_table = _MAN_PST[not up]
    own_pass = _PASS[up]
    enemy_pass = _PASS[not up]
    sparse = total <= 8

    pieces = men
    while pieces:
        bit = pieces & -pieces
        s = bit.bit_length() - 1
        advancement = (s >> 3) if up else (7 - (s >> 3))
        score += own_table[s]
        if sparse:
            score += 2 * advancement
        if not enemy_kings and advancement >= 3:
            if not (own_pass[s] & enemy_men):
                score += 12 + 3 * (advancement - 3)
        pieces ^= bit

    pieces = enemy_men
    while pieces:
        bit = pieces & -pieces
        s = bit.bit_length() - 1
        advancement = (7 - (s >> 3)) if up else (s >> 3)
        score -= enemy_table[s]
        if sparse:
            score -= 2 * advancement
        if not kings and advancement >= 3:
            if not (enemy_pass[s] & men):
                score -= 12 + 3 * (advancement - 3)
        pieces ^= bit

    pieces = kings
    while pieces:
        bit = pieces & -pieces
        score += _KING_PST[bit.bit_length() - 1]
        pieces ^= bit

    pieces = enemy_kings
    while pieces:
        bit = pieces & -pieces
        score -= _KING_PST[bit.bit_length() - 1]
        pieces ^= bit

    score += 2 * (mobility.bit_count() - enemy_mobility.bit_count())
    score += 2 * (
        (men & _neighbors(own)).bit_count()
        - (enemy_men & _neighbors(enemy)).bit_count()
    )

    guard_value = 5 if total > 12 else (2 if total > 6 else 0)
    score += guard_value * (
        (men & _HOME[up]).bit_count()
        - (enemy_men & _HOME[not up]).bit_count()
    )

    if total <= 6:
        if material >= 75:
            score += _pursuit(kings, enemy)
        elif material <= -75:
            score -= _pursuit(enemy_kings, own)

    return score


class _Engine:
    __slots__ = (
        "deadline", "nodes", "tt", "history", "killers",
        "path", "past", "root_best"
    )

    def __init__(self, deadline, past):
        self.deadline = deadline
        self.nodes = 0
        self.tt = _TT
        self.history = _HISTORY
        self.killers = [[None, None] for _ in range(128)]
        self.path = set()
        self.past = past
        self.root_best = None

    def order(self, moves, men, kings, enemy_kings, up, ply, tt_move):
        if len(moves) < 2:
            return
        history = self.history[up]
        killer1, killer2 = self.killers[ply]
        table = _MAN_PST[up]
        crown = _CROWN[up]

        def priority(move):
            if move == tt_move:
                return 1000000000
            f = move & 63
            t = (move >> 6) & 63
            is_king = bool(kings & (1 << f))
            pst = _KING_PST if is_king else table
            value = 3 * (pst[t] - pst[f])

            if move & 4096:
                captured = 1 << ((f + t) >> 1)
                value += 20000
                value += 1000 if captured & enemy_kings else 100
                if is_king:
                    value -= 10
            else:
                value += history[move]
                if move == killer1:
                    value += 8000
                elif move == killer2:
                    value += 6000

            if not is_king and ((1 << t) & crown):
                value += 12000
            return value

        moves.sort(key=priority, reverse=True)

    def store(self, key, depth, value, flag, move, ply, old):
        if old is not None and old[0] > depth:
            return
        if value > 29000:
            value += ply
        elif value < -29000:
            value -= ply
        self.tt[key] = (depth, flag, value, move)

    def search(self, men, kings, enemy_men, enemy_kings,
               up, depth, alpha, beta, ply):
        self.nodes += 1
        if (self.nodes & 127) == 0:
            if time.perf_counter() >= self.deadline:
                raise _Timeout

        if not (men | kings):
            return -_MATE + ply
        if not (enemy_men | enemy_kings):
            return _MATE - ply

        key = (men, kings, enemy_men, enemy_kings, up)
        if ply and (key in self.path or key in self.past):
            return 0

        original_alpha = alpha
        old = self.tt.get(key)
        tt_move = None
        if old is not None:
            stored_depth, flag, value, tt_move = old
            if value > 29000:
                value -= ply
            elif value < -29000:
                value += ply

            if stored_depth >= depth:
                usable = (
                    flag == 0
                    or (flag == 1 and value >= beta)
                    or (flag == 2 and value <= alpha)
                )
                if usable:
                    if ply == 0:
                        self.root_best = tt_move
                    return value

        moves = _captures(men, kings, enemy_men, enemy_kings, up)
        capturing = bool(moves)

        if depth == 0 and not capturing:
            value = _evaluate(
                men, kings, enemy_men, enemy_kings, up, ply
            )
            self.store(key, 0, value, 0, None, ply, old)
            return value

        if not capturing:
            moves = _steps(men, kings, enemy_men, enemy_kings, up)
            if not moves:
                value = -_MATE + ply
                self.store(key, depth, value, 0, None, ply, old)
                return value

        self.order(moves, men, kings, enemy_kings, up, ply, tt_move)
        self.path.add(key)

        best_value = -_INF
        best_move = moves[0]
        next_depth = max(0, depth - 1)
        crown = _CROWN[up]
        next_up = not up
        can_reduce = (
            depth >= 3 and not capturing and ply > 0
            and (men | kings | enemy_men | enemy_kings).bit_count() > 8
        )

        for index, move in enumerate(moves):
            f = move & 63
            t = (move >> 6) & 63
            source = 1 << f
            target = 1 << t
            promoted = False

            if source & men:
                new_men = men ^ source
                new_kings = kings
                if target & crown:
                    new_kings |= target
                    promoted = True
                else:
                    new_men |= target
            else:
                new_men = men
                new_kings = kings ^ source ^ target

            new_enemy_men = enemy_men
            new_enemy_kings = enemy_kings
            if capturing:
                captured = 1 << ((f + t) >> 1)
                new_enemy_men &= ~captured
                new_enemy_kings &= ~captured

            if index == 0:
                value = -self.search(
                    new_enemy_men, new_enemy_kings,
                    new_men, new_kings, next_up,
                    next_depth, -beta, -alpha, ply + 1
                )
            else:
                reduction = int(
                    can_reduce and index >= 4 and not promoted
                    and move not in self.killers[ply]
                )
                value = -self.search(
                    new_enemy_men, new_enemy_kings,
                    new_men, new_kings, next_up,
                    next_depth - reduction,
                    -alpha - 1, -alpha, ply + 1
                )
                if reduction and value > alpha:
                    value = -self.search(
                        new_enemy_men, new_enemy_kings,
                        new_men, new_kings, next_up,
                        next_depth, -alpha - 1, -alpha, ply + 1
                    )
                if alpha < value < beta:
                    value = -self.search(
                        new_enemy_men, new_enemy_kings,
                        new_men, new_kings, next_up,
                        next_depth, -beta, -alpha, ply + 1
                    )

            if value > best_value:
                best_value = value
                best_move = move
            if value > alpha:
                alpha = value
            if alpha >= beta:
                if not capturing:
                    killers = self.killers[ply]
                    if move != killers[0]:
                        killers[1] = killers[0]
                        killers[0] = move
                    history = self.history[up]
                    history[move] = min(
                        200000, history[move] + 4 * depth * depth
                    )
                break

        self.path.remove(key)

        if best_value <= original_alpha:
            flag = 2
        elif best_value >= beta:
            flag = 1
        else:
            flag = 0
        self.store(key, depth, best_value, flag, best_move, ply, old)

        if ply == 0:
            self.root_best = best_move
        return best_value


def _decode(move):
    f = move & 63
    t = (move >> 6) & 63
    return ((f >> 3, f & 7), (t >> 3, t & 7))


def policy(my_men, my_kings, opp_men, opp_kings, color):
    global _LAST_TOTAL, _HISTORY

    started = time.perf_counter()
    deadline = started + 0.90

    men = _bits(my_men)
    kings = _bits(my_kings)
    enemy_men = _bits(opp_men)
    enemy_kings = _bits(opp_kings)
    up = color == "w"

    total = (men | kings | enemy_men | enemy_kings).bit_count()
    if total > _LAST_TOTAL:
        _TT.clear()
        _RECENT.clear()
    _LAST_TOTAL = total

    if len(_TT) > 100000:
        _TT.clear()

    moves = _captures(men, kings, enemy_men, enemy_kings, up)
    if not moves:
        moves = _steps(men, kings, enemy_men, enemy_kings, up)

    # A terminal position has no legal action under the supplied API.
    if not moves:
        raise ValueError("No legal move exists in this terminal position.")

    key = (men, kings, enemy_men, enemy_kings, up)
    past = frozenset(_RECENT)
    _RECENT.append(key)
    if len(_RECENT) > 80:
        del _RECENT[0]

    if len(moves) == 1:
        return _decode(moves[0])

    _HISTORY = [[value // 2 for value in row] for row in _HISTORY]
    engine = _Engine(deadline, past)

    old = _TT.get(key)
    preferred = old[3] if old is not None else None
    engine.order(moves, men, kings, enemy_kings, up, 0, preferred)
    chosen = moves[0]
    legal = set(moves)
    last_score = 0

    try:
        for depth in range(1, 40):
            if time.perf_counter() >= deadline:
                break

            if depth >= 4:
                alpha, beta = last_score - 40, last_score + 40
            else:
                alpha, beta = -_INF, _INF

            score = engine.search(
                men, kings, enemy_men, enemy_kings,
                up, depth, alpha, beta, 0
            )

            if score <= alpha or score >= beta:
                if time.perf_counter() >= deadline:
                    break
                score = engine.search(
                    men, kings, enemy_men, enemy_kings,
                    up, depth, -_INF, _INF, 0
                )

            if engine.root_best in legal:
                chosen = engine.root_best
            last_score = score

            if abs(score) > 29000:
                break

    except _Timeout:
        pass

    return _decode(chosen)
