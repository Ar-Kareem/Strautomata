
import time

BOARD_SIZE = 6
FULL_BOARD = (1 << 36) - 1
MATE = 1_000_000
INF = 2_000_000

NORMAL = 2
WIN = 1
DRAW = 0
LOSS = -1


def _make_win_masks():
    masks = []

    # Horizontal five-cell windows.
    for r in range(6):
        for c in range(2):
            mask = 0
            for i in range(5):
                mask |= 1 << (r * 6 + c + i)
            masks.append(mask)

    # Vertical five-cell windows.
    for r in range(2):
        for c in range(6):
            mask = 0
            for i in range(5):
                mask |= 1 << ((r + i) * 6 + c)
            masks.append(mask)

    # Down-right diagonals.
    for r in range(2):
        for c in range(2):
            mask = 0
            for i in range(5):
                mask |= 1 << ((r + i) * 6 + c + i)
            masks.append(mask)

    # Down-left diagonals.
    for r in range(2):
        for c in range(4, 6):
            mask = 0
            for i in range(5):
                mask |= 1 << ((r + i) * 6 + c - i)
            masks.append(mask)

    return tuple(masks)


WIN_MASKS = _make_win_masks()

H_START = sum(1 << (r * 6 + c) for r in range(6) for c in range(2))
V_START = sum(1 << (r * 6 + c) for r in range(2) for c in range(6))
D_START = sum(1 << (r * 6 + c) for r in range(2) for c in range(2))
A_START = sum(1 << (r * 6 + c) for r in range(2) for c in range(4, 6))

CENTER_MASK = (
    (1 << (1 * 6 + 1))
    | (1 << (1 * 6 + 4))
    | (1 << (4 * 6 + 1))
    | (1 << (4 * 6 + 4))
)


def _has_win(bits):
    x = bits & (bits >> 1) & (bits >> 2) & (bits >> 3) & (bits >> 4)
    if x & H_START:
        return True

    x = bits & (bits >> 6) & (bits >> 12) & (bits >> 18) & (bits >> 24)
    if x & V_START:
        return True

    x = bits & (bits >> 7) & (bits >> 14) & (bits >> 21) & (bits >> 28)
    if x & D_START:
        return True

    x = bits & (bits >> 5) & (bits >> 10) & (bits >> 15) & (bits >> 20)
    return bool(x & A_START)


def _make_rotation_data():
    permutations = []
    destination_bits = []

    for quadrant in range(4):
        base_r = (quadrant // 2) * 3
        base_c = (quadrant % 2) * 3

        for direction in range(2):  # 0 = L, 1 = R
            permutation = list(range(36))

            for r in range(base_r, base_r + 3):
                for c in range(base_c, base_c + 3):
                    local_r = r - base_r
                    local_c = c - base_c

                    if direction == 1:  # Clockwise
                        new_r = base_r + local_c
                        new_c = base_c + 2 - local_r
                    else:  # Anticlockwise
                        new_r = base_r + 2 - local_c
                        new_c = base_c + local_r

                    permutation[r * 6 + c] = new_r * 6 + new_c

            permutations.append(tuple(permutation))
            destination_bits.append(
                tuple(1 << permutation[position] for position in range(36))
            )

    # Table indexed by rotation, source row, and six-bit source-row value.
    rotation_tables = []
    for permutation in permutations:
        row_tables = []
        for row in range(6):
            table = [0] * 64
            for value in range(64):
                result = 0
                for col in range(6):
                    if value & (1 << col):
                        source = row * 6 + col
                        result |= 1 << permutation[source]
                table[value] = result
            row_tables.append(tuple(table))
        rotation_tables.append(tuple(row_tables))

    return tuple(rotation_tables), tuple(destination_bits)


ROTATION_TABLES, DESTINATION_BITS = _make_rotation_data()


def _rotate(bits, rotation):
    table = ROTATION_TABLES[rotation]
    return (
        table[0][bits & 63]
        | table[1][(bits >> 6) & 63]
        | table[2][(bits >> 12) & 63]
        | table[3][(bits >> 18) & 63]
        | table[4][(bits >> 24) & 63]
        | table[5][(bits >> 30) & 63]
    )


def _state_id(a, b):
    return a | (b << 36)


class _Timeout(Exception):
    pass


class _Engine:
    def __init__(self, deadline):
        self.deadline = deadline
        self.nodes = 0
        self.eval_cache = {}
        self.children_cache = {}
        self.tt = {}
        self.best_hint = {}

    def check_time(self):
        if time.perf_counter() >= self.deadline:
            raise _Timeout

    def evaluate(self, a, b):
        key = _state_id(a, b)
        cached = self.eval_cache.get(key)
        if cached is not None:
            return cached

        # Increasing value for one through four uncontested marbles in a
        # possible five-cell winning window.
        weights = (0, 3, 18, 110, 900, 0)
        score = 0

        for mask in WIN_MASKS:
            ca = (a & mask).bit_count()
            cb = (b & mask).bit_count()

            if cb == 0:
                score += weights[ca]
            elif ca == 0:
                score -= weights[cb]

        # Quadrant centers do not move when their quadrant is rotated.
        score += 9 * (
            (a & CENTER_MASK).bit_count() - (b & CENTER_MASK).bit_count()
        )

        self.eval_cache[key] = score
        return score

    def children(self, a, b):
        key = (a, b)
        cached = self.children_cache.get(key)
        if cached is not None:
            return cached

        self.check_time()

        empty = FULL_BOARD ^ (a | b)
        board_becomes_full = (empty & (empty - 1)) == 0
        result = []
        seen = set()

        # A record is:
        # (ordering_score, new_a, new_b, original_position, rotation, status)
        for rotation in range(8):
            self.check_time()
            rotated_a = _rotate(a, rotation)
            rotated_b = _rotate(b, rotation)
            opponent_wins = _has_win(rotated_b)
            destinations = DESTINATION_BITS[rotation]

            remaining = empty
            while remaining:
                least_bit = remaining & -remaining
                position = least_bit.bit_length() - 1
                remaining ^= least_bit

                new_a = rotated_a | destinations[position]
                new_b = rotated_b
                sid = _state_id(new_a, new_b)

                if sid in seen:
                    continue
                seen.add(sid)

                player_wins = _has_win(new_a)

                if player_wins and not opponent_wins:
                    status = WIN
                    ordering_score = MATE
                elif opponent_wins and not player_wins:
                    status = LOSS
                    ordering_score = -MATE
                elif player_wins or opponent_wins or board_becomes_full:
                    status = DRAW
                    ordering_score = 0
                else:
                    status = NORMAL
                    ordering_score = self.evaluate(new_a, new_b)

                result.append(
                    (
                        ordering_score,
                        new_a,
                        new_b,
                        position,
                        rotation,
                        status,
                    )
                )

        result.sort(key=lambda item: item[0], reverse=True)
        self.children_cache[key] = result
        return result

    @staticmethod
    def terminal_value(status, next_ply):
        if status == WIN:
            return MATE - next_ply
        if status == LOSS:
            return -MATE + next_ply
        return 0

    def negamax(self, a, b, depth, alpha, beta, ply):
        self.nodes += 1
        if (self.nodes & 63) == 0:
            self.check_time()

        if depth <= 0:
            return self.evaluate(a, b)

        original_alpha = alpha
        original_beta = beta
        tt_key = (a, b, depth)
        entry = self.tt.get(tt_key)

        if entry is not None:
            value, flag = entry
            if flag == 0:
                return value
            if flag == 1:  # Lower bound
                if value > alpha:
                    alpha = value
            else:  # Upper bound
                if value < beta:
                    beta = value
            if alpha >= beta:
                return value

        moves = self.children(a, b)
        hint = self.best_hint.get((a, b))

        if hint is not None:
            hint_index = -1
            for i, move in enumerate(moves):
                if _state_id(move[1], move[2]) == hint:
                    hint_index = i
                    break
            if hint_index > 0:
                ordered = (
                    [moves[hint_index]]
                    + moves[:hint_index]
                    + moves[hint_index + 1 :]
                )
            else:
                ordered = moves
        else:
            ordered = moves

        best = -INF
        best_state = None

        for move in ordered:
            ordering_score, new_a, new_b, _, _, status = move

            if status != NORMAL:
                value = self.terminal_value(status, ply + 1)
            elif depth == 1:
                value = ordering_score
            else:
                value = -self.negamax(
                    new_b, new_a, depth - 1, -beta, -alpha, ply + 1
                )

            if value > best:
                best = value
                best_state = _state_id(new_a, new_b)

            if value > alpha:
                alpha = value
            if alpha >= beta:
                break

        if best_state is not None:
            self.best_hint[(a, b)] = best_state

        if best <= original_alpha:
            flag = 2  # Upper bound
        elif best >= original_beta:
            flag = 1  # Lower bound
        else:
            flag = 0  # Exact

        self.tt[tt_key] = (best, flag)
        return best

    def root_search(self, a, b, depth, previous_values, selective):
        moves = self.children(a, b)

        if previous_values:
            ordered = sorted(
                moves,
                key=lambda move: previous_values.get(
                    _state_id(move[1], move[2]), move[0]
                ),
                reverse=True,
            )
        else:
            ordered = moves

        # In the normal midgame, depth three is selective only at the root.
        # Every opponent response and every tactical continuation beneath a
        # selected move is still searched exhaustively.
        if selective and depth >= 3 and len(ordered) > 14:
            ordered = ordered[:14]

        alpha = -INF
        beta = INF
        best_value = -INF
        best_move = ordered[0]
        values = {}

        for move in ordered:
            self.check_time()
            ordering_score, new_a, new_b, _, _, status = move

            if status != NORMAL:
                value = self.terminal_value(status, 1)
            elif depth == 1:
                value = ordering_score
            else:
                value = -self.negamax(
                    new_b, new_a, depth - 1, -beta, -alpha, 1
                )

            values[_state_id(new_a, new_b)] = value

            if value > best_value:
                best_value = value
                best_move = move

            if value > alpha:
                alpha = value

        return best_value, best_move, values


def _format_move(move):
    position = move[3]
    rotation = move[4]
    row = position // 6 + 1
    col = position % 6 + 1
    quadrant = rotation // 2
    direction = "L" if rotation % 2 == 0 else "R"
    return f"{row},{col},{quadrant},{direction}"


def policy(you, opponent) -> str:
    own_bits = 0
    opponent_bits = 0
    first_empty = None

    for r in range(6):
        for c in range(6):
            bit = 1 << (r * 6 + c)
            if int(you[r][c]):
                own_bits |= bit
            elif int(opponent[r][c]):
                opponent_bits |= bit
            elif first_empty is None:
                first_empty = r * 6 + c

    # Guaranteed legal fallback, established before any search.
    fallback_row = first_empty // 6 + 1
    fallback_col = first_empty % 6 + 1
    fallback = f"{fallback_row},{fallback_col},0,L"

    occupied_count = (own_bits | opponent_bits).bit_count()

    # Strong, rotation-invariant opening: the center of a quadrant.
    if occupied_count == 0:
        return "2,2,0,R"

    engine = _Engine(time.perf_counter() + 0.93)

    try:
        root_moves = engine.children(own_bits, opponent_bits)
    except _Timeout:
        return fallback

    if not root_moves:
        return fallback

    chosen = root_moves[0]

    # Never overlook a win available on this move.
    for move in root_moves:
        if move[5] == WIN:
            return _format_move(move)

    remaining_cells = 36 - occupied_count

    # Complete depth two is the main tactical guarantee. In short endgames,
    # iterative deepening is allowed to continue toward an exact solution.
    if remaining_cells <= 6:
        maximum_depth = remaining_cells
        selective = False
    else:
        maximum_depth = 3
        selective = True

    previous_values = {}

    for depth in range(1, maximum_depth + 1):
        try:
            _, best_move, values = engine.root_search(
                own_bits,
                opponent_bits,
                depth,
                previous_values,
                selective,
            )
        except _Timeout:
            break

        chosen = best_move
        previous_values = values

    return _format_move(chosen)
