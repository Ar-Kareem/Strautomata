
from time import perf_counter

_ROWS = 5
_COLS = 6
_FULL = (1 << 30) - 1
_LEFT = sum(1 << (6 * r) for r in range(5))
_RIGHT = _LEFT << 5
_NOT_LEFT = _FULL ^ _LEFT
_NOT_RIGHT = _FULL ^ _RIGHT

_WIN = 1_000_000
_INF = _WIN + 1000


def _neighbors(x):
    return (
        (x << 6)
        | (x >> 6)
        | ((x & _NOT_RIGHT) << 1)
        | ((x & _NOT_LEFT) >> 1)
    ) & _FULL


_NEIGHBOR = {1 << i: _neighbors(1 << i) for i in range(30)}


def _moves(a, b):
    result = []

    sources = a & (b << 6)
    while sources:
        s = sources & -sources
        sources ^= s
        result.append((s, s >> 6))

    sources = a & _NOT_RIGHT & (b >> 1)
    while sources:
        s = sources & -sources
        sources ^= s
        result.append((s, s << 1))

    sources = a & (b >> 6)
    while sources:
        s = sources & -sources
        sources ^= s
        result.append((s, s << 6))

    sources = a & _NOT_LEFT & (b << 1)
    while sources:
        s = sources & -sources
        sources ^= s
        result.append((s, s >> 1))

    return result


def _edge_count(x, y):
    return (
        ((x << 6) & y).bit_count()
        + ((x >> 6) & y).bit_count()
        + (((x & _NOT_RIGHT) << 1) & y).bit_count()
        + (((x & _NOT_LEFT) >> 1) & y).bit_count()
    )


def _static(a, b):
    na = _neighbors(a)
    nb = _neighbors(b)

    supported_a = a & na
    supported_b = b & nb
    front_a = a & nb
    front_b = b & na

    pressure = (
        _edge_count(supported_a, b)
        - _edge_count(supported_b, a)
    )
    supported_front = (
        (supported_a & nb).bit_count()
        - (supported_b & na).bit_count()
    )
    reserves = (
        (a & _neighbors(front_a)).bit_count()
        - (b & _neighbors(front_b)).bit_count()
    )

    return 16 * pressure + 6 * supported_front + 2 * reserves + 3


def _read_board(board):
    bits = 0
    if len(board) == 30:
        for i in range(30):
            if board[i]:
                bits |= 1 << i
    else:
        for r in range(5):
            row = board[r]
            for c in range(6):
                if row[c]:
                    bits |= 1 << (6 * r + c)
    return bits


def _format_move(move):
    s, t = move
    i = s.bit_length() - 1
    j = t.bit_length() - 1
    difference = j - i
    direction = {-6: "U", 1: "R", 6: "D", -1: "L"}[difference]
    return f"{i // 6},{i % 6},{direction}"


class _Timeout(Exception):
    pass


class _Engine:
    def __init__(self, deadline):
        self.deadline = deadline
        self.ticks = 0

        self.tt = {}
        self.history = {}
        self.killers = [None] * 32
        self.parts_cache = {}

        # A game is (left_options, right_options).
        # Each option is a normalized tuple representing a sum of games.
        zero = ((), ())
        star = (((),), ((),))
        self.games = [zero, star]
        self.negative = [0, 1]
        self.game_ids = {zero: 0, star: 1}

        self.compiled = {}
        self.sum_wins = {
            ((), 0): False,
            ((), 1): False,
        }

    def tick(self):
        self.ticks += 1
        if (self.ticks & 127) == 0:
            if perf_counter() >= self.deadline:
                raise _Timeout

    def parts(self, occupied):
        cached = self.parts_cache.get(occupied)
        if cached is not None:
            return cached

        remaining = occupied
        result = []
        while remaining:
            component = remaining & -remaining
            frontier = component
            while frontier:
                frontier = _neighbors(frontier) & remaining & ~component
                component |= frontier
            remaining ^= component
            result.append(component)

        result = tuple(result)
        self.parts_cache[occupied] = result
        return result

    def normalize(self, sequence):
        # G + (-G) is zero; self-negative games cancel in pairs.
        result = []
        negative = self.negative
        for game in sequence:
            if not game:
                continue
            opposite = negative[game]
            if opposite in result:
                result.remove(opposite)
            else:
                result.append(game)
        result.sort()
        return tuple(result)

    def negate_sum(self, state):
        return tuple(sorted(self.negative[g] for g in state))

    def sum_win(self, state, turn):
        self.tick()
        key = (state, turn)
        cached = self.sum_wins.get(key)
        if cached is not None:
            return cached

        previous = -1
        for i, game in enumerate(state):
            if game == previous:
                continue
            previous = game
            rest = state[:i] + state[i + 1:]

            for option in self.games[game][turn]:
                following = self.normalize(rest + option)
                if not self.sum_win(following, 1 - turn):
                    self.sum_wins[key] = True
                    return True

        self.sum_wins[key] = False
        return False

    def intern_game(self, left, right):
        definition = (left, right)
        existing = self.game_ids.get(definition)
        if existing is not None:
            return existing

        negative_definition = (
            tuple(sorted(self.negate_sum(s) for s in right)),
            tuple(sorted(self.negate_sum(s) for s in left)),
        )

        game = len(self.games)
        self.games.append(definition)
        self.negative.append(0)
        self.game_ids[definition] = game

        if negative_definition == definition:
            self.negative[game] = game
        else:
            opposite = len(self.games)
            self.games.append(negative_definition)
            self.negative.append(game)
            self.negative[game] = opposite
            self.game_ids[negative_definition] = opposite

        left_wins = self.sum_win((game,), 0)
        right_wins = self.sum_win((game,), 1)

        # A game in which both players lose moving first equals zero.
        if not left_wins and not right_wins:
            self.game_ids[definition] = 0
            self.game_ids[negative_definition] = 0
            return 0

        # Recognize additional representations of the impartial game *.
        if left_wins and right_wins:
            with_star = self.normalize((game, 1))
            if (
                not self.sum_win(with_star, 0)
                and not self.sum_win(with_star, 1)
            ):
                self.game_ids[definition] = 1
                self.game_ids[negative_definition] = 1
                return 1

        return game

    def save_compiled(self, a, b, result):
        self.compiled[a | (b << 30)] = result
        self.compiled[b | (a << 30)] = self.negate_sum(result)
        return result

    def compile_position(self, a, b):
        self.tick()
        key = a | (b << 30)
        cached = self.compiled.get(key)
        if cached is not None:
            return cached

        if not (a & _neighbors(b)):
            return self.save_compiled(a, b, ())

        mixed = [
            c for c in self.parts(a | b)
            if (c & a) and (c & b)
        ]

        if len(mixed) != 1 or mixed[0] != (a | b):
            terms = []
            for component in mixed:
                terms.extend(
                    self.compile_position(a & component, b & component)
                )
            result = self.normalize(terms)
            return self.save_compiled(a, b, result)

        # An isolated bichromatic star is exactly *.
        if (
            (a.bit_count() == 1 or b.bit_count() == 1)
            and not (a & _neighbors(a))
            and not (b & _neighbors(b))
        ):
            return self.save_compiled(a, b, (1,))

        left = tuple(sorted({
            self.compile_position(a ^ s ^ t, b ^ t)
            for s, t in _moves(a, b)
        }))
        right = tuple(sorted({
            self.compile_position(a ^ t, b ^ s ^ t)
            for s, t in _moves(b, a)
        }))

        game = self.intern_game(left, right)
        result = () if game == 0 else (game,)
        return self.save_compiled(a, b, result)

    def endgame(self, a, b):
        mixed = []
        for component in self.parts(a | b):
            if not (component & a) or not (component & b):
                continue
            if component.bit_count() > 7:
                return None
            mixed.append(component)

        terms = []
        for component in mixed:
            terms.extend(
                self.compile_position(a & component, b & component)
            )

        state = self.normalize(terms)
        return _WIN if self.sum_win(state, 0) else -_WIN

    def order_score(self, move, a, b, depth, hash_move, killer):
        if move == hash_move:
            return 10**12
        if move == killer:
            return 10**10

        s, t = move
        aa = a ^ s ^ t
        bb = b ^ t

        if not (bb & _neighbors(aa)):
            return 10**11

        history = self.history.get(move, 0)
        if depth >= 3:
            positional = _static(aa, bb)
        else:
            positional = (
                12 * (_NEIGHBOR[s] & a).bit_count()
                - 16 * (_NEIGHBOR[t] & b).bit_count()
                + 5 * (_NEIGHBOR[t] & a & ~s).bit_count()
            )

        return 8 * positional + 3 * history

    def search(self, a, b, depth, alpha, beta, ply):
        self.tick()

        if not (a & _neighbors(b)):
            return -_WIN

        key = a | (b << 30)
        entry = self.tt.get(key)
        hash_move = None

        if entry is not None:
            saved_depth, saved_score, flag, hash_move = entry
            if saved_depth >= depth:
                if flag == 0:
                    return saved_score
                if flag == 1 and saved_score >= beta:
                    return saved_score
                if flag == 2 and saved_score <= alpha:
                    return saved_score

        if ply and (a | b).bit_count() <= 20:
            exact = self.endgame(a, b)
            if exact is not None:
                self.tt[key] = (99, exact, 0, None)
                return exact

        if depth <= 0:
            return _static(a, b)

        moves = _moves(a, b)
        killer = self.killers[ply]
        moves.sort(
            key=lambda m: self.order_score(
                m, a, b, depth, hash_move, killer
            ),
            reverse=True,
        )

        original_alpha = alpha
        best_score = -_INF
        best_move = moves[0]

        for index, move in enumerate(moves):
            s, t = move
            child_a = b ^ t
            child_b = a ^ s ^ t

            if index == 0 or depth < 3:
                score = -self.search(
                    child_a, child_b, depth - 1,
                    -beta, -alpha, ply + 1
                )
            else:
                score = -self.search(
                    child_a, child_b, depth - 1,
                    -alpha - 1, -alpha, ply + 1
                )
                if alpha < score < beta and score != _WIN:
                    score = -self.search(
                        child_a, child_b, depth - 1,
                        -beta, -alpha, ply + 1
                    )

            if score > best_score:
                best_score = score
                best_move = move

            if score > alpha:
                alpha = score

            if alpha >= beta or best_score == _WIN:
                self.killers[ply] = move
                self.history[move] = (
                    self.history.get(move, 0) + depth * depth
                )
                break

        if best_score == _WIN:
            flag = 0
        elif best_score <= original_alpha:
            flag = 2
        elif best_score >= beta:
            flag = 1
        else:
            flag = 0

        self.tt[key] = (depth, best_score, flag, best_move)
        return best_score


def policy(you: list[int], opponent: list[int]) -> str:
    started = perf_counter()
    a = _read_board(you)
    b = _read_board(opponent)
    legal = _moves(a, b)

    # Terminal positions have no legal move and are not normally queried.
    if not legal:
        return "0,0,U"

    if len(legal) == 1:
        return _format_move(legal[0])

    # Establish a legal fallback before starting timed search.
    best_move = legal[0]
    best_fallback_score = -_INF
    for move in legal:
        s, t = move
        aa = a ^ s ^ t
        bb = b ^ t
        if not (bb & _neighbors(aa)):
            return _format_move(move)

        score = _static(aa, bb)
        if score > best_fallback_score:
            best_fallback_score = score
            best_move = move

    engine = _Engine(started + 0.88)
    root_key = a | (b << 30)
    previous_score = 0
    maximum_depth = (a | b).bit_count() - 1

    try:
        for depth in range(1, maximum_depth + 1):
            if perf_counter() >= engine.deadline:
                break

            alpha, beta = -_INF, _INF
            if depth >= 4 and abs(previous_score) < _WIN // 2:
                alpha = previous_score - 120
                beta = previous_score + 120

            score = engine.search(a, b, depth, alpha, beta, 0)

            if (
                abs(score) != _WIN
                and (score <= alpha or score >= beta)
            ):
                score = engine.search(
                    a, b, depth, -_INF, _INF, 0
                )

            root_entry = engine.tt.get(root_key)
            if root_entry is not None and root_entry[3] in legal:
                best_move = root_entry[3]

            previous_score = score
            if abs(score) == _WIN:
                break

    except _Timeout:
        pass

    return _format_move(best_move)
