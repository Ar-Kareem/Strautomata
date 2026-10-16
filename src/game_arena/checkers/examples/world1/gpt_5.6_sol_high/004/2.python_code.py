
import time

# Colors are represented internally as BLACK = 0 and WHITE = 1.
BLACK = 0
WHITE = 1

INF = 1_000_000_000
MATE = 10_000_000

EXACT = 0
LOWER = 1
UPPER = 2


class SearchTimeout(Exception):
    pass


# Board geometry and move tables.
ROW = [sq // 8 for sq in range(64)]
COL = [sq % 8 for sq in range(64)]

MEN_STEPS = [[[] for _ in range(64)] for _ in range(2)]
MEN_JUMPS = [[[] for _ in range(64)] for _ in range(2)]
KING_STEPS = [[] for _ in range(64)]
KING_JUMPS = [[] for _ in range(64)]

for sq in range(64):
    r, c = ROW[sq], COL[sq]

    for dr, dc in ((1, -1), (1, 1), (-1, -1), (-1, 1)):
        r1, c1 = r + dr, c + dc
        if 0 <= r1 < 8 and 0 <= c1 < 8:
            KING_STEPS[sq].append(r1 * 8 + c1)

        r2, c2 = r + 2 * dr, c + 2 * dc
        if (0 <= r1 < 8 and 0 <= c1 < 8 and
                0 <= r2 < 8 and 0 <= c2 < 8):
            KING_JUMPS[sq].append((r2 * 8 + c2, r1 * 8 + c1))

    for color, dr in ((BLACK, -1), (WHITE, 1)):
        for dc in (-1, 1):
            r1, c1 = r + dr, c + dc
            if 0 <= r1 < 8 and 0 <= c1 < 8:
                MEN_STEPS[color][sq].append(r1 * 8 + c1)

            r2, c2 = r + 2 * dr, c + 2 * dc
            if (0 <= r1 < 8 and 0 <= c1 < 8 and
                    0 <= r2 < 8 and 0 <= c2 < 8):
                MEN_JUMPS[color][sq].append(
                    (r2 * 8 + c2, r1 * 8 + c1)
                )


# Positional values include the basic material value.
MAN_VALUE = [[0] * 64 for _ in range(2)]
KING_VALUE = [0] * 64

for sq in range(64):
    r, c = ROW[sq], COL[sq]
    center_depth = min(r, 7 - r, c, 7 - c)
    central = 2 <= r <= 5 and 2 <= c <= 5
    edge = c == 0 or c == 7

    for color in (BLACK, WHITE):
        advancement = (7 - r) if color == BLACK else r
        value = 100 + 4 * advancement + advancement * advancement

        if central:
            value += 4
        if edge:
            value += 2
        if advancement == 0:
            value += 7

        MAN_VALUE[color][sq] = value

    king_value = 178 + 4 * center_depth
    if edge:
        king_value += 1
    if (r in (0, 7)) and (c in (0, 7)):
        king_value -= 3
    KING_VALUE[sq] = king_value


# These tables persist between calls and can therefore reuse analysis from
# earlier positions in the same game.
TRANSPOSITION = {}
HISTORY = {}
KILLERS = {}

DEADLINE = 0.0
NODES = 0


def _check_time():
    global NODES
    NODES += 1
    if (NODES & 127) == 0 and time.perf_counter() >= DEADLINE:
        raise SearchTimeout


def _iter_bits(bits):
    while bits:
        low = bits & -bits
        yield low.bit_length() - 1
        bits ^= low


def _generate_moves(men, kings, opp_men, opp_kings, color):
    """Return (source, destination, captured_square), honoring captures."""
    occupied = men | kings | opp_men | opp_kings
    opponents = opp_men | opp_kings
    captures = []

    bits = men
    while bits:
        low = bits & -bits
        src = low.bit_length() - 1
        bits ^= low

        for dst, middle in MEN_JUMPS[color][src]:
            if ((opponents >> middle) & 1) and not ((occupied >> dst) & 1):
                captures.append((src, dst, middle))

    bits = kings
    while bits:
        low = bits & -bits
        src = low.bit_length() - 1
        bits ^= low

        for dst, middle in KING_JUMPS[src]:
            if ((opponents >> middle) & 1) and not ((occupied >> dst) & 1):
                captures.append((src, dst, middle))

    if captures:
        return captures

    moves = []

    bits = men
    while bits:
        low = bits & -bits
        src = low.bit_length() - 1
        bits ^= low

        for dst in MEN_STEPS[color][src]:
            if not ((occupied >> dst) & 1):
                moves.append((src, dst, -1))

    bits = kings
    while bits:
        low = bits & -bits
        src = low.bit_length() - 1
        bits ^= low

        for dst in KING_STEPS[src]:
            if not ((occupied >> dst) & 1):
                moves.append((src, dst, -1))

    return moves


def _make_move(men, kings, opp_men, opp_kings, color, move):
    src, dst, captured = move
    src_bit = 1 << src
    dst_bit = 1 << dst

    if men & src_bit:
        men ^= src_bit
        promotion_row = 0 if color == BLACK else 7
        if ROW[dst] == promotion_row:
            kings |= dst_bit
        else:
            men |= dst_bit
    else:
        kings ^= src_bit
        kings |= dst_bit

    if captured >= 0:
        captured_bit = 1 << captured
        if opp_men & captured_bit:
            opp_men ^= captured_bit
        else:
            opp_kings ^= captured_bit

    return men, kings, opp_men, opp_kings


def _mobility(men, kings, occupied, color):
    count = 0

    bits = men
    while bits:
        low = bits & -bits
        src = low.bit_length() - 1
        bits ^= low
        for dst in MEN_STEPS[color][src]:
            if not ((occupied >> dst) & 1):
                count += 1

    bits = kings
    while bits:
        low = bits & -bits
        src = low.bit_length() - 1
        bits ^= low
        for dst in KING_STEPS[src]:
            if not ((occupied >> dst) & 1):
                count += 1

    return count


def _side_score(men, kings, color):
    score = 0

    bits = men
    while bits:
        low = bits & -bits
        sq = low.bit_length() - 1
        bits ^= low
        score += MAN_VALUE[color][sq]

    bits = kings
    while bits:
        low = bits & -bits
        sq = low.bit_length() - 1
        bits ^= low
        score += KING_VALUE[sq]

    # Reward men protected by a friendly piece behind them.
    friendly = men | kings
    bits = men
    support_dr = -1 if color == WHITE else 1
    while bits:
        low = bits & -bits
        sq = low.bit_length() - 1
        bits ^= low
        r, c = ROW[sq], COL[sq]

        supported = False
        rr = r + support_dr
        if 0 <= rr < 8:
            for cc in (c - 1, c + 1):
                if 0 <= cc < 8 and ((friendly >> (rr * 8 + cc)) & 1):
                    supported = True
                    break
        if supported:
            score += 3

    # A pair of back-rank guards is useful against easy promotion.
    back_row = 7 if color == BLACK else 0
    back_count = 0
    for c in range(8):
        if (men >> (back_row * 8 + c)) & 1:
            back_count += 1
    if back_count >= 2:
        score += 6

    return score


def _evaluate(men, kings, opp_men, opp_kings, color):
    occupied = men | kings | opp_men | opp_kings

    own_score = _side_score(men, kings, color)
    opp_score = _side_score(opp_men, opp_kings, 1 - color)

    own_mobility = _mobility(men, kings, occupied, color)
    opp_mobility = _mobility(opp_men, opp_kings, occupied, 1 - color)

    score = own_score - opp_score
    score += 2 * (own_mobility - opp_mobility)

    # In sparse endings, active kings and mobility become more important.
    piece_count = occupied.bit_count()
    if piece_count <= 8:
        score += own_mobility - opp_mobility

    return score


def _move_order_score(move, men, kings, opp_men, opp_kings,
                      color, ply, tt_move):
    if move == tt_move:
        return 10_000_000

    src, dst, captured = move
    score = 0

    if captured >= 0:
        score += 1_000_000
        captured_bit = 1 << captured
        if opp_kings & captured_bit:
            score += 30_000
        else:
            score += 15_000

        if men & (1 << src):
            promotion_row = 0 if color == BLACK else 7
            if ROW[dst] == promotion_row:
                score += 20_000
    else:
        killers = KILLERS.get(ply)
        if killers:
            if move == killers[0]:
                score += 100_000
            elif len(killers) > 1 and move == killers[1]:
                score += 80_000

        score += HISTORY.get((color, src, dst), 0)

        if men & (1 << src):
            score += MAN_VALUE[color][dst] - MAN_VALUE[color][src]
            promotion_row = 0 if color == BLACK else 7
            if ROW[dst] == promotion_row:
                score += 50_000
        else:
            score += KING_VALUE[dst] - KING_VALUE[src]

    return score


def _ordered_moves(moves, men, kings, opp_men, opp_kings,
                   color, ply, tt_move=None):
    return sorted(
        moves,
        key=lambda mv: _move_order_score(
            mv, men, kings, opp_men, opp_kings, color, ply, tt_move
        ),
        reverse=True
    )


def _record_cutoff(move, color, depth, ply):
    src, dst, captured = move
    if captured < 0:
        key = (color, src, dst)
        HISTORY[key] = min(200_000, HISTORY.get(key, 0) + depth * depth)

        killers = KILLERS.setdefault(ply, [])
        if not killers or killers[0] != move:
            if move in killers:
                killers.remove(move)
            killers.insert(0, move)
            if len(killers) > 2:
                killers.pop()


def _quiescence(men, kings, opp_men, opp_kings,
                color, alpha, beta, ply):
    _check_time()

    moves = _generate_moves(men, kings, opp_men, opp_kings, color)

    if not moves:
        return -MATE + ply

    # If there is no mandatory capture, the tactical sequence is settled.
    if moves[0][2] < 0:
        return _evaluate(men, kings, opp_men, opp_kings, color)

    moves = _ordered_moves(
        moves, men, kings, opp_men, opp_kings, color, ply
    )

    best = -INF

    for move in moves:
        nm, nk, nom, nok = _make_move(
            men, kings, opp_men, opp_kings, color, move
        )

        value = -_quiescence(
            nom, nok, nm, nk, 1 - color, -beta, -alpha, ply + 1
        )

        if value > best:
            best = value
        if value > alpha:
            alpha = value
        if alpha >= beta:
            break

    return best


def _negamax(men, kings, opp_men, opp_kings,
             color, depth, alpha, beta, ply):
    _check_time()

    if depth <= 0:
        return _quiescence(
            men, kings, opp_men, opp_kings, color, alpha, beta, ply
        )

    key = (men, kings, opp_men, opp_kings, color)
    alpha_start = alpha
    beta_start = beta
    entry = TRANSPOSITION.get(key)
    tt_move = None

    if entry is not None:
        stored_depth, stored_value, flag, tt_move = entry
        if stored_depth >= depth:
            if flag == EXACT:
                return stored_value
            if flag == LOWER:
                alpha = max(alpha, stored_value)
            else:
                beta = min(beta, stored_value)
            if alpha >= beta:
                return stored_value

    moves = _generate_moves(men, kings, opp_men, opp_kings, color)

    if not moves:
        return -MATE + ply

    moves = _ordered_moves(
        moves, men, kings, opp_men, opp_kings, color, ply, tt_move
    )

    best_value = -INF
    best_move = moves[0]

    for index, move in enumerate(moves):
        nm, nk, nom, nok = _make_move(
            men, kings, opp_men, opp_kings, color, move
        )

        if index == 0:
            value = -_negamax(
                nom, nok, nm, nk, 1 - color,
                depth - 1, -beta, -alpha, ply + 1
            )
        else:
            # Principal variation search: first try a narrow window.
            value = -_negamax(
                nom, nok, nm, nk, 1 - color,
                depth - 1, -alpha - 1, -alpha, ply + 1
            )
            if alpha < value < beta:
                value = -_negamax(
                    nom, nok, nm, nk, 1 - color,
                    depth - 1, -beta, -alpha, ply + 1
                )

        if value > best_value:
            best_value = value
            best_move = move

        if value > alpha:
            alpha = value

        if alpha >= beta:
            _record_cutoff(move, color, depth, ply)
            break

    if best_value <= alpha_start:
        flag = UPPER
    elif best_value >= beta_start:
        flag = LOWER
    else:
        flag = EXACT

    if len(TRANSPOSITION) < 220_000 or key in TRANSPOSITION:
        TRANSPOSITION[key] = (depth, best_value, flag, best_move)

    return best_value


def _search_root(men, kings, opp_men, opp_kings,
                 color, moves, depth, preferred_move):
    key = (men, kings, opp_men, opp_kings, color)
    entry = TRANSPOSITION.get(key)
    tt_move = preferred_move

    if tt_move is None and entry is not None:
        tt_move = entry[3]

    ordered = _ordered_moves(
        moves, men, kings, opp_men, opp_kings, color, 0, tt_move
    )

    alpha = -INF
    beta = INF
    best_value = -INF
    best_move = ordered[0]

    for index, move in enumerate(ordered):
        if time.perf_counter() >= DEADLINE:
            raise SearchTimeout

        nm, nk, nom, nok = _make_move(
            men, kings, opp_men, opp_kings, color, move
        )

        if index == 0:
            value = -_negamax(
                nom, nok, nm, nk, 1 - color,
                depth - 1, -beta, -alpha, 1
            )
        else:
            value = -_negamax(
                nom, nok, nm, nk, 1 - color,
                depth - 1, -alpha - 1, -alpha, 1
            )
            if value > alpha:
                value = -_negamax(
                    nom, nok, nm, nk, 1 - color,
                    depth - 1, -beta, -alpha, 1
                )

        if value > best_value:
            best_value = value
            best_move = move

        if value > alpha:
            alpha = value

    if len(TRANSPOSITION) < 220_000 or key in TRANSPOSITION:
        TRANSPOSITION[key] = (depth, best_value, EXACT, best_move)

    return best_value, best_move


def _to_bitboard(squares):
    board = 0
    for row, col in squares:
        board |= 1 << (row * 8 + col)
    return board


def policy(my_men, my_kings, opp_men, opp_kings, color) \
        -> tuple[tuple[int, int], tuple[int, int]]:
    global DEADLINE, NODES

    start_time = time.perf_counter()
    DEADLINE = start_time + 0.88
    NODES = 0

    if len(TRANSPOSITION) > 180_000:
        TRANSPOSITION.clear()

    internal_color = WHITE if str(color).lower() == "w" else BLACK

    men = _to_bitboard(my_men)
    kings = _to_bitboard(my_kings)
    enemy_men = _to_bitboard(opp_men)
    enemy_kings = _to_bitboard(opp_kings)

    legal_moves = _generate_moves(
        men, kings, enemy_men, enemy_kings, internal_color
    )

    # Terminal positions should not be sent to policy. This fallback keeps the
    # function total in case such a position is supplied.
    if not legal_moves:
        if my_men:
            square = tuple(my_men[0])
            return square, square
        if my_kings:
            square = tuple(my_kings[0])
            return square, square
        return (0, 0), (0, 0)

    if len(legal_moves) == 1:
        src, dst, _ = legal_moves[0]
        return (ROW[src], COL[src]), (ROW[dst], COL[dst])

    # Establish a strategically ordered legal fallback before timed search.
    ordered_fallback = _ordered_moves(
        legal_moves, men, kings, enemy_men, enemy_kings,
        internal_color, 0
    )
    best_move = ordered_fallback[0]
    preferred_move = best_move

    total_pieces = (
        men | kings | enemy_men | enemy_kings
    ).bit_count()

    if total_pieces <= 6:
        maximum_depth = 28
    elif total_pieces <= 10:
        maximum_depth = 22
    else:
        maximum_depth = 16

    try:
        for depth in range(1, maximum_depth + 1):
            value, completed_move = _search_root(
                men, kings, enemy_men, enemy_kings,
                internal_color, legal_moves, depth, preferred_move
            )

            best_move = completed_move
            preferred_move = completed_move

            # A forced win has been proven within the current horizon.
            if value >= MATE - 100:
                break

            # Avoid beginning another iteration with almost no time left.
            if time.perf_counter() >= DEADLINE - 0.025:
                break

    except SearchTimeout:
        pass

    src, dst, _ = best_move
    return (ROW[src], COL[src]), (ROW[dst], COL[dst])
