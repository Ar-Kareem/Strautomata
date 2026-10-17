
import time

_FULL = (1 << 36) - 1
_MATE = 1_000_000
_INF = 2_000_000


def _index(r, c):
    return ((r // 3) * 2 + c // 3) * 9 + (r % 3) * 3 + c % 3


def _indices(mask):
    result = []
    while mask:
        bit = mask & -mask
        result.append(bit.bit_length() - 1)
        mask ^= bit
    return tuple(result)


# Every length-five winning segment, including the two windows
# in each length-six line.
_lines = []
for _r in range(6):
    for _c in range(6):
        for _dr, _dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
            _er = _r + 4 * _dr
            _ec = _c + 4 * _dc
            if 0 <= _er < 6 and 0 <= _ec < 6:
                _mask = 0
                for _k in range(5):
                    _mask |= 1 << _index(_r + _k * _dr, _c + _k * _dc)
                _lines.append(_mask)
_LINES = tuple(_lines)

# Fast iteration over all possible empty subsets of a winning segment.
_CELLS = {0: ()}
for _mask in _LINES:
    _sub = _mask
    while _sub:
        if _sub not in _CELLS:
            _CELLS[_sub] = _indices(_sub)
        _sub = (_sub - 1) & _mask

# Each quadrant occupies nine consecutive bits.
_rotations = []
_maps = []
for _q in range(4):
    for _clockwise in (False, True):
        _local_map = []
        for _i in range(9):
            _rr, _cc = divmod(_i, 3)
            if _clockwise:
                _j = _cc * 3 + (2 - _rr)
            else:
                _j = (2 - _cc) * 3 + _rr
            _local_map.append(_j)

        _table = [0] * 512
        for _x in range(1, 512):
            _bit = _x & -_x
            _i = _bit.bit_length() - 1
            _table[_x] = _table[_x ^ _bit] | (1 << _local_map[_i])

        _mapping = list(range(36))
        for _i in range(9):
            _mapping[9 * _q + _i] = 9 * _q + _local_map[_i]

        _shift = 9 * _q
        _rotations.append(
            (_shift, _FULL ^ (511 << _shift), tuple(_table))
        )
        _maps.append(tuple(_mapping))

_ROTATIONS = tuple(_rotations)
_MAPS = tuple(_maps)
_BITS = tuple(1 << i for i in range(36))
_CENTERS = sum(1 << (9 * q + 4) for q in range(4))
_POINTS = tuple(5 if i % 9 == 4 else 0 for i in range(36))

_WEIGHTS = (0, 2, 14, 90, 600, 0)
_INCREMENTS = (2, 12, 76, 510)


class _Timeout(Exception):
    pass


class _Engine:
    def __init__(self, deadline):
        self.deadline = deadline
        self.rotation_cache = {}
        self.tactical_cache = {}
        self.tt = {}
        self.ticks = 0

    def check_time(self):
        if time.perf_counter() >= self.deadline:
            raise _Timeout

    def rotated(self, board):
        result = self.rotation_cache.get(board)
        if result is None:
            result = tuple(
                (board & keep) | (table[(board >> shift) & 511] << shift)
                for shift, keep, table in _ROTATIONS
            )
            self.rotation_cache[board] = result
        return result

    def can_win(self, a, b):
        """Whether a has a legal move winning outright, not merely drawing."""
        self.ticks += 1
        if not (self.ticks & 31):
            self.check_time()

        key = (a, b)
        cached = self.tactical_cache.get(key)
        if cached is not None:
            return cached

        if (a | b) == _FULL:
            self.tactical_cache[key] = False
            return False

        seen = set()
        for ar, br in zip(self.rotated(a), self.rotated(b)):
            pair = (ar, br)
            if pair in seen:
                continue
            seen.add(pair)

            not_a = _FULL ^ ar
            possible = False
            for line in _LINES:
                missing = line & not_a
                if not (missing & (missing - 1)) and not (missing & br):
                    possible = True
                    break

            if possible:
                # Placement cannot remove an opponent five already
                # produced by this rotation.
                enemy_five = False
                for line in _LINES:
                    if br & line == line:
                        enemy_five = True
                        break
                if not enemy_five:
                    self.tactical_cache[key] = True
                    return True

        self.tactical_cache[key] = False
        return False

    def moves(self, a, b):
        """
        Entries are:
          (heuristic, resulting_a, resulting_b, encoded_action, terminal)
        terminal: 0 ongoing, 1 win, -1 loss, 2 draw.
        """
        self.check_time()
        empty = _indices(_FULL ^ (a | b))
        if not empty:
            return []

        last_cell = len(empty) == 1
        center_score = 5 * (
            (a & _CENTERS).bit_count() - (b & _CENTERS).bit_count()
        )

        result = []
        draw_move = None
        loss_move = None
        seen_rotations = set()
        seen_children = set()

        for rotation, (ar, br) in enumerate(
            zip(self.rotated(a), self.rotated(b))
        ):
            pair = (ar, br)
            if pair in seen_rotations:
                continue
            seen_rotations.add(pair)

            base = center_score
            delta = list(_POINTS)
            winning_cells = 0
            enemy_five = False

            for line in _LINES:
                own = ar & line
                enemy = br & line

                if not enemy:
                    count = own.bit_count()
                    base += _WEIGHTS[count]

                    if count == 5:
                        winning_cells = _FULL
                    elif count == 4:
                        winning_cells |= line ^ own
                    else:
                        increment = _INCREMENTS[count]
                        for cell in _CELLS[line ^ own]:
                            delta[cell] += increment

                elif not own:
                    count = enemy.bit_count()
                    if count == 5:
                        enemy_five = True
                    else:
                        weight = _WEIGHTS[count]
                        base -= weight
                        for cell in _CELLS[line ^ enemy]:
                            delta[cell] += weight

            mapping = _MAPS[rotation]
            for original_cell in empty:
                cell = mapping[original_cell]
                bit = _BITS[cell]
                child_a = ar | bit
                action = original_cell * 8 + rotation

                if winning_cells & bit:
                    if not enemy_five:
                        move = (_MATE, child_a, br, action, 1)
                        self.tactical_cache[(a, b)] = True
                        return [move]
                    if draw_move is None:
                        draw_move = (0, child_a, br, action, 2)
                    continue

                if enemy_five:
                    if loss_move is None:
                        loss_move = (-_MATE, child_a, br, action, -1)
                    continue

                if last_cell:
                    if draw_move is None:
                        draw_move = (0, child_a, br, action, 2)
                    continue

                child_key = (child_a, br)
                if child_key in seen_children:
                    continue
                seen_children.add(child_key)
                result.append((base + delta[cell], child_a, br, action, 0))

        if draw_move is not None:
            result.append(draw_move)
        if loss_move is not None:
            result.append(loss_move)

        result.sort(key=lambda move: move[0], reverse=True)
        self.tactical_cache[(a, b)] = False
        return result

    def search(self, a, b, depth, alpha, beta, ply):
        self.check_time()
        key = (a, b)
        entry = self.tt.get(key)
        preferred = None

        if entry is not None:
            old_depth, flag, value, preferred = entry
            if old_depth >= depth:
                if flag == 0:
                    return value
                if flag == 1:
                    alpha = max(alpha, value)
                else:
                    beta = min(beta, value)
                if alpha >= beta:
                    return value

        original_alpha, original_beta = alpha, beta
        moves = self.moves(a, b)
        if not moves:
            return 0

        if moves[0][4] == 1:
            value = _MATE - ply
            self.tt[key] = (depth, 0, value, moves[0][3])
            return value

        # At the frontier, find the highest-scoring move that does not
        # allow an immediate reply win. This considers every legal move
        # when necessary, rather than pruning away a low-scoring defense.
        if depth == 1:
            best = -_INF
            best_action = moves[0][3]
            for score, ca, cb, action, terminal in moves:
                if terminal == 2:
                    best, best_action = 0, action
                    break
                if terminal == -1:
                    value = -_MATE + ply
                elif self.can_win(cb, ca):
                    value = -_MATE + ply + 1
                else:
                    best, best_action = score, action
                    break

                if value > best:
                    best, best_action = value, action

            self.tt[key] = (depth, 0, best, best_action)
            return best

        if preferred is not None:
            for i, move in enumerate(moves):
                if move[3] == preferred:
                    if i:
                        moves.insert(0, moves.pop(i))
                    break

        remaining = 36 - (a | b).bit_count()
        if remaining <= 8:
            width = len(moves)
        elif remaining <= 12:
            width = 24
        elif ply <= 1:
            width = 14
        elif ply == 2:
            width = 10
        else:
            width = 8

        best = -_INF
        best_action = moves[0][3]
        searched_safe = 0

        for score, ca, cb, action, terminal in moves:
            if terminal == 2:
                value = 0
                searched_safe += 1
            elif terminal == -1:
                value = -_MATE + ply
            elif self.can_win(cb, ca):
                value = -_MATE + ply + 1
            else:
                searched_safe += 1
                value = -self.search(
                    cb, ca, depth - 1, -beta, -alpha, ply + 1
                )

            if value > best:
                best, best_action = value, action
            if value > alpha:
                alpha = value
            if alpha >= beta:
                break

            # Never conclude a forced loss just because the beam's
            # highest-ranked defenses all failed.
            if searched_safe >= width and best > -_MATE // 2:
                break

        if best <= original_alpha:
            flag = -1
        elif best >= original_beta:
            flag = 1
        else:
            flag = 0
        self.tt[key] = (depth, flag, best, best_action)
        return best


def _format_move(action):
    cell, rotation = divmod(action, 8)
    quadrant, local = divmod(cell, 9)
    r, c = divmod(local, 3)
    r += 3 * (quadrant // 2)
    c += 3 * (quadrant % 2)
    direction = "R" if rotation & 1 else "L"
    return f"{r + 1},{c + 1},{rotation // 2},{direction}"


def policy(you, opponent) -> str:
    start = time.perf_counter()
    a = 0
    b = 0

    for r in range(6):
        for c in range(6):
            bit = 1 << _index(r, c)
            if you[r][c]:
                a |= bit
            elif opponent[r][c]:
                b |= bit

    empty_mask = _FULL ^ (a | b)
    first_empty = (empty_mask & -empty_mask).bit_length() - 1
    fallback = first_empty * 8

    if not (a | b):
        return "2,2,0,L"

    engine = _Engine(start + 0.90)
    completed_depth = 1
    partial_action = None

    try:
        moves = engine.moves(a, b)
        if not moves:
            return _format_move(fallback)

        fallback = moves[0][3]
        if moves[0][4] == 1:
            return _format_move(fallback)

        roots = []
        for move in moves:
            _, ca, cb, action, terminal = move
            if terminal == -1:
                continue
            if terminal == 2 or not engine.can_win(cb, ca):
                roots.append(move)
                if len(roots) == 1:
                    fallback = action

        if not roots:
            return _format_move(fallback)
        if len(roots) == 1:
            return _format_move(roots[0][3])
        if all(move[4] == 2 for move in roots):
            return _format_move(roots[0][3])

        remaining = empty_mask.bit_count()
        if remaining > 22:
            root_width = 28
        elif remaining > 14:
            root_width = 36
        elif remaining > 8:
            root_width = 48
        else:
            root_width = len(roots)

        previous_scores = {move[3]: move[0] for move in roots}

        for depth in range(2, min(8, remaining) + 1):
            engine.check_time()
            alpha = -_INF
            iteration_best = -_INF
            iteration_action = fallback
            partial_action = None
            new_scores = dict(previous_scores)

            # The first deeper pass examines every safe root move.
            limit = len(roots) if depth == 2 else root_width

            for number, move in enumerate(roots):
                engine.check_time()
                _, ca, cb, action, terminal = move

                if terminal == 2:
                    value = 0
                else:
                    value = -engine.search(
                        cb, ca, depth - 1, -_INF, -alpha, 1
                    )

                new_scores[action] = value
                if value > iteration_best:
                    iteration_best = value
                    iteration_action = action
                    partial_action = action

                if value > alpha:
                    alpha = value

                if value > _MATE // 2:
                    return _format_move(action)

                if number + 1 >= limit and iteration_best > -_MATE // 2:
                    break

            fallback = iteration_action
            completed_depth = depth
            previous_scores = new_scores
            roots.sort(
                key=lambda move: (
                    move[3] == fallback,
                    previous_scores[move[3]],
                    move[0],
                ),
                reverse=True,
            )

    except _Timeout:
        if completed_depth == 1 and partial_action is not None:
            fallback = partial_action

    return _format_move(fallback)
